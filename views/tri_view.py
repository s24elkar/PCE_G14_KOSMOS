"""
VUE - Page de tri KOSMOS
Architecture MVC - Vue uniquement
Affiche les 6 angles de la vidéo sélectionnée (toutes les 30s)
Lecture vidéo au survol + Métadonnées depuis JSON
"""
import sys
import os
import json
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QSplitter,
    QGridLayout, QLineEdit, QMenu, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QThread, QTimer, QEvent
from PyQt6.QtGui import QFont, QAction, QPalette, QColor, QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

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
# WIDGET VIDÉO AVEC PREVIEW AU SURVOL
# ═══════════════════════════════════════════════════════════════

class VideoPreviewLabel(QLabel):
    """Label qui affiche une vidéo au survol"""
    
    def __init__(self, angle_num, timestamp, parent=None):
        super().__init__(parent)
        self.angle_num = angle_num
        self.timestamp = timestamp
        self.video_path = None
        self.hover_active = False
        
        # Configuration du label
        self.setMinimumSize(180, 100)
        self.setMaximumSize(280, 160)
        self.setStyleSheet("background-color: #2a2a2a; border: none; color: #888;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("📹")
        self.setScaledContents(True)
        
        # Activer le tracking de la souris
        self.setMouseTracking(True)
        
        # Player vidéo (créé à la demande)
        self.media_player = None
        self.video_widget = None
        self.audio_output = None
    
    def set_video_path(self, path):
        """Définit le chemin de la vidéo pour le preview"""
        self.video_path = path
    
    def enterEvent(self, event):
        """Survol : démarre la lecture vidéo"""
        if self.video_path and os.path.exists(self.video_path):
            self.start_video_preview()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Sortie survol : arrête la lecture"""
        self.stop_video_preview()
        super().leaveEvent(event)
    
    def start_video_preview(self):
        """Démarre la lecture vidéo au timestamp"""
        try:
            # Créer le player si nécessaire
            if not self.media_player:
                self.media_player = QMediaPlayer()
                self.audio_output = QAudioOutput()
                self.audio_output.setVolume(0)  # Muet
                self.media_player.setAudioOutput(self.audio_output)
                
                # Créer le widget vidéo
                self.video_widget = QVideoWidget()
                self.video_widget.setStyleSheet("background-color: black;")
                
                # Remplacer le layout
                if self.layout():
                    QWidget().setLayout(self.layout())
                
                layout = QVBoxLayout(self)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.video_widget)
                
                self.media_player.setVideoOutput(self.video_widget)
            
            # Charger et lire la vidéo
            from PyQt6.QtCore import QUrl
            self.media_player.setSource(QUrl.fromLocalFile(self.video_path))
            self.media_player.setPosition(self.timestamp * 1000)  # ms
            self.media_player.play()
            
            self.hover_active = True
            print(f"▶️ Lecture preview angle {self.angle_num} à {self.timestamp}s")
            
        except Exception as e:
            print(f"⚠️ Erreur preview vidéo: {e}")
    
    def stop_video_preview(self):
        """Arrête la lecture vidéo"""
        if self.media_player and self.hover_active:
            self.media_player.stop()
            self.hover_active = False
            print(f"⏸️ Arrêt preview angle {self.angle_num}")


# ═══════════════════════════════════════════════════════════════
# EXTRACTION DES ANGLES (THREAD)
# ═══════════════════════════════════════════════════════════════

class AngleExtractor(QThread):
    """Thread pour extraire les 6 angles d'une vidéo (toutes les 30 secondes)"""
    angle_ready = pyqtSignal(int, QPixmap)
    
    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        
    def run(self):
        """Extrait les 6 angles"""
        for idx in range(6):
            try:
                timestamp = idx * 30  # 0, 30, 60, 90, 120, 150 secondes
                pixmap = self.extract_frame_at_time(self.video_path, timestamp)
                if pixmap:
                    self.angle_ready.emit(idx, pixmap)
            except Exception as e:
                print(f"⚠️ Erreur extraction angle {idx+1}: {e}")
    
    def extract_frame_at_time(self, video_path, timestamp):
        """Extrait une frame à un timestamp donné"""
        if not os.path.exists(video_path):
            print(f"⚠️ Fichier vidéo non trouvé: {video_path}")
            return None
        
        try:
            temp_dir = Path(video_path).parent / ".angles"
            temp_dir.mkdir(exist_ok=True)
            
            angle_path = temp_dir / f"angle_{Path(video_path).stem}_{timestamp}s.jpg"
            
            if angle_path.exists():
                pixmap = QPixmap(str(angle_path))
                if not pixmap.isNull():
                    return pixmap
            
            hours = timestamp // 3600
            minutes = (timestamp % 3600) // 60
            seconds = timestamp % 60
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            cmd = ['ffmpeg', '-i', video_path, '-ss', time_str, '-vframes', '1', '-vf', 'scale=320:-1', '-y', str(angle_path)]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            
            if result.returncode == 0 and angle_path.exists():
                pixmap = QPixmap(str(angle_path))
                return pixmap
            
        except subprocess.TimeoutExpired:
            print(f"⚠️ Timeout extraction angle")
        except FileNotFoundError:
            print(f"⚠️ ffmpeg non trouvé")
        except Exception as e:
            print(f"⚠️ Erreur: {e}")
        
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
            self.tabs = ["Fichier", "Tri", "Extraction", "Évènements"]
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
        self.angle_extractor = None
        self.init_ui()
        self.connecter_signaux()
        self.charger_videos()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.navbar = NavBarAvecMenu(tabs=["Fichier", "Tri", "Extraction", "Évènements"], default_tab="Tri")
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
        
        angles_widget = QWidget()
        angles_layout = QGridLayout()
        angles_layout.setSpacing(6)
        angles_layout.setContentsMargins(8, 8, 8, 8)
        
        self.angle_labels = []
        for row in range(2):
            for col in range(3):
                angle_num = row * 3 + col + 1
                timestamp = (angle_num - 1) * 30
                
                angle_frame = QFrame()
                angle_frame.setStyleSheet("background-color: #2a2a2a; border: 1px solid #555;")
                angle_layout = QVBoxLayout()
                angle_layout.setContentsMargins(0, 0, 0, 0)
                angle_layout.setSpacing(0)
                
                # NOUVEAU : Utiliser VideoPreviewLabel au lieu de QLabel
                img_label = VideoPreviewLabel(angle_num, timestamp)
                
                time_label = QLabel(f"Angle {angle_num} - {timestamp}s")
                time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                time_label.setStyleSheet("color: white; font-size: 9px; padding: 2px; background-color: #1a1a1a;")
                
                angle_layout.addWidget(img_label)
                angle_layout.addWidget(time_label)
                angle_frame.setLayout(angle_layout)
                
                angles_layout.addWidget(angle_frame, row, col)
                self.angle_labels.append(img_label)
        
        for i in range(2):
            angles_layout.setRowStretch(i, 1)
        for i in range(3):
            angles_layout.setColumnStretch(i, 1)
        
        angles_widget.setLayout(angles_layout)
        apercu_layout.addWidget(angles_widget)
        apercu_container.setLayout(apercu_layout)
        
        layout.addWidget(apercu_container, stretch=1)
        
        # MÉTADONNÉES
        meta_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        meta_communes_widget = self.create_metadata_section("Métadonnées communes", readonly=False, type_meta="communes")
        meta_splitter.addWidget(meta_communes_widget)
        
        meta_propres_widget = self.create_metadata_section("Métadonnées propres", readonly=False, type_meta="propres")
        meta_splitter.addWidget(meta_propres_widget)
        
        meta_splitter.setStretchFactor(0, 1)
        meta_splitter.setStretchFactor(1, 1)
        
        layout.addWidget(meta_splitter, stretch=1)
        
        panel.setLayout(layout)
        return panel
    
    def create_metadata_section(self, title, readonly=False, type_meta="communes"):
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
        
        if type_meta == "communes":
            self.meta_communes_fields = {}
            for key in ['system', 'camera', 'model', 'version']:
                row = self.create_metadata_row(key, readonly=False)
                self.meta_communes_fields[key] = row['widget']
                content_layout.addWidget(row['container'])
            
            content_layout.addStretch()
            
            btn_modifier_communes = QPushButton("Modifier")
            btn_modifier_communes.setFixedSize(90, 26)
            btn_modifier_communes.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_modifier_communes.setStyleSheet("QPushButton { background-color: transparent; color: white; border: 2px solid white; border-radius: 4px; font-size: 10px; font-weight: bold; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }")
            btn_modifier_communes.clicked.connect(self.on_modifier_metadata_communes)
            
            btn_layout_c = QHBoxLayout()
            btn_layout_c.addStretch()
            btn_layout_c.addWidget(btn_modifier_communes)
            btn_layout_c.setContentsMargins(0, 4, 0, 4)
            content_layout.addLayout(btn_layout_c)
            
        else:
            self.meta_propres_fields = {}
            self.meta_propres_widgets = {}
            
            for key in ['campaign', 'zone', 'zoneDict']:
                row = self.create_metadata_row(key, readonly=False)
                self.meta_propres_fields[key] = row['widget']
                self.meta_propres_widgets[key] = row['container']
                content_layout.addWidget(row['container'])
            
            content_layout.addStretch()
            
            btn_modifier = QPushButton("Modifier")
            btn_modifier.setFixedSize(90, 26)
            btn_modifier.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_modifier.setStyleSheet("QPushButton { background-color: transparent; color: white; border: 2px solid white; border-radius: 4px; font-size: 10px; font-weight: bold; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }")
            btn_modifier.clicked.connect(self.on_modifier_metadata_propres)
            
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
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
        label.setFixedWidth(65)
        row_layout.addWidget(label)
        
        value_widget = QLineEdit()
        value_widget.setStyleSheet("color: white; padding: 3px; background-color: #1a1a1a; border: 1px solid #555; font-size: 10px;")
        
        row_layout.addWidget(value_widget)
        row_widget.setLayout(row_layout)
        
        return {'container': row_widget, 'widget': value_widget}
    
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
        
        # Sélectionner et afficher la première vidéo par défaut
        if len(videos) > 0:
            self.table.selectRow(0)
            self.controller.selectionner_video(videos[0].nom)
    
    def charger_metadata_depuis_json(self, video):
        """Charge les métadonnées depuis le fichier JSON du dossier"""
        try:
            dossier = Path(video.chemin).parent
            json_path = dossier / f"{video.dossier_numero}.json"
            
            if not json_path.exists():
                print(f"⚠️ Fichier JSON non trouvé: {json_path}")
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # MÉTADONNÉES COMMUNES (system)
            if 'system' in data:
                system = data['system']
                video.metadata_communes['system'] = system.get('system', '')
                video.metadata_communes['camera'] = system.get('camera', '')
                video.metadata_communes['model'] = system.get('model', '')
                video.metadata_communes['version'] = system.get('version', '')
            
            # MÉTADONNÉES PROPRES (campaign)
            if 'campaign' in data:
                campaign = data['campaign']
                if 'zoneDict' in campaign:
                    zone_dict = campaign['zoneDict']
                    video.metadata_propres['campaign'] = zone_dict.get('campaign', '')
                    video.metadata_propres['zone'] = zone_dict.get('zone', '')
                    video.metadata_propres['zone_dict'] = str(zone_dict)
            
            print(f"✅ Métadonnées JSON chargées pour {video.nom}")
            print(f"   Communes: {video.metadata_communes}")
            print(f"   Propres: {video.metadata_propres}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lecture JSON: {e}")
            return False
    
    def extraire_angles(self, video_path):
        """Lance l'extraction des 6 angles de la vidéo"""
        for label in self.angle_labels:
            label.clear()
            label.setText("⏳")
            label.setStyleSheet("background-color: #2a2a2a; border: none; color: #888;")
            # Définir le chemin vidéo pour le preview
            label.set_video_path(video_path)
        
        if self.angle_extractor and self.angle_extractor.isRunning():
            self.angle_extractor.terminate()
        
        self.angle_extractor = AngleExtractor(video_path)
        self.angle_extractor.angle_ready.connect(self.afficher_angle)
        self.angle_extractor.start()
        
        print(f"🎬 Extraction des 6 angles lancée...")
    
    def afficher_angle(self, index, pixmap):
        """Affiche un angle extrait"""
        if index < len(self.angle_labels):
            self.angle_labels[index].setPixmap(pixmap)
            self.angle_labels[index].setText("")
            print(f"✅ Angle {index+1} affiché")
    
    def on_video_selected(self):
        selected = self.table.selectedItems()
        if selected and self.controller:
            row = selected[0].row()
            nom_video = self.table.item(row, 0).text()
            self.controller.selectionner_video(nom_video)
    
    def afficher_video(self, video):
        self.video_selectionnee = video
        
        print(f"\n📹 Vidéo sélectionnée : {video.nom}")
        
        # Charger les métadonnées depuis le JSON
        self.charger_metadata_depuis_json(video)
        
        print(f"   Métadonnées communes : {video.metadata_communes}")
        print(f"   Métadonnées propres : {video.metadata_propres}")
        
        # Métadonnées communes
        self.meta_communes_fields['system'].setText(video.metadata_communes.get('system', ''))
        self.meta_communes_fields['camera'].setText(video.metadata_communes.get('camera', ''))
        self.meta_communes_fields['model'].setText(video.metadata_communes.get('model', ''))
        self.meta_communes_fields['version'].setText(video.metadata_communes.get('version', ''))
        
        # Métadonnées propres
        self.meta_propres_fields['campaign'].setText(video.metadata_propres.get('campaign', ''))
        self.meta_propres_fields['zone'].setText(video.metadata_propres.get('zone', ''))
        self.meta_propres_fields['zoneDict'].setText(video.metadata_propres.get('zone_dict', ''))
        
        # Extraire les angles de la vidéo
        self.extraire_angles(video.chemin)
    
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
            
            if nouveau_nom == self.video_selectionnee.nom:
                return
            
            reponse = QMessageBox.question(
                self,
                "Confirmer le renommage",
                f"Voulez-vous vraiment renommer :\n\n'{self.video_selectionnee.nom}'\n\nen\n\n'{nouveau_nom}' ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reponse == QMessageBox.StandardButton.Yes:
                if self.controller.renommer_video(self.video_selectionnee.nom, nouveau_nom):
                    QMessageBox.information(self, "Succès", f"Vidéo renommée en '{nouveau_nom}'")
                    self.charger_videos()
                    print(f"✅ Vidéo renommée : {self.video_selectionnee.nom} → {nouveau_nom}")
                else:
                    QMessageBox.critical(self, "Erreur", "Impossible de renommer la vidéo.")
    
    def on_supprimer(self):
        if not self.video_selectionnee:
            QMessageBox.warning(self, "Aucune vidéo", "Veuillez sélectionner une vidéo à supprimer.")
            return
        
        reponse = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer la vidéo :\n\n'{self.video_selectionnee.nom}' ?\n\nCette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reponse == QMessageBox.StandardButton.Yes:
            if self.controller.supprimer_video(self.video_selectionnee.nom):
                QMessageBox.information(self, "Succès", f"Vidéo '{self.video_selectionnee.nom}' marquée pour suppression")
                self.charger_videos()
                print(f"🗑️ Vidéo supprimée : {self.video_selectionnee.nom}")
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de supprimer la vidéo.")
    
    def on_modifier_metadata_communes(self):
        if self.video_selectionnee and self.controller:
            nouvelles_meta = {
                'system': self.meta_communes_fields['system'].text(),
                'camera': self.meta_communes_fields['camera'].text(),
                'model': self.meta_communes_fields['model'].text(),
                'version': self.meta_communes_fields['version'].text()
            }
            
            if self.controller.modifier_metadonnees_communes(self.video_selectionnee.nom, nouvelles_meta):
                QMessageBox.information(self, "Succès", "Métadonnées communes modifiées et sauvegardées!")
                print(f"✅ Métadonnées communes sauvegardées")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de sauvegarder les métadonnées")
    
    def on_modifier_metadata_propres(self):
        if self.video_selectionnee and self.controller:
            nouvelles_meta = {
                'campaign': self.meta_propres_fields['campaign'].text(),
                'zone': self.meta_propres_fields['zone'].text(),
                'zone_dict': self.meta_propres_fields['zoneDict'].text()
            }
            
            if self.controller.modifier_metadonnees_propres(self.video_selectionnee.nom, nouvelles_meta):
                QMessageBox.information(self, "Succès", "Métadonnées propres modifiées et sauvegardées!")
                print(f"✅ Métadonnées propres sauvegardées")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de sauvegarder les métadonnées")


# TEST
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from models.app_model import ApplicationModel
    except ImportError:
        print("❌ Impossible d'importer ApplicationModel")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    font = QFont("Montserrat", 10)
    app.setFont(font)
    
    model = ApplicationModel()
    campagne = model.creer_campagne("Test_Tri", "./test_campagne")
    
    for i in range(15):
        video = type('Video', (), {
            'nom': f'0{113+i}.mp4',
            'chemin': f'/test/0{113+i}.mp4',
            'dossier_numero': f'0{113+i}',
            'taille': f'{1.0 + i*0.1:.1f} Go',
            'duree': '15:01',
            'date': '21/08/2025',
            'metadata_communes': {
                'system': 'Kstereo',
                'camera': 'imx477',
                'model': 'Raspberry Pi 5',
                'version': '4.0'
            },
            'metadata_propres': {
                'campaign': 'ATL',
                'zone': 'CC',
                'zone_dict': 'Zone_test'
            },
            'est_selectionnee': False,
            'est_conservee': True
        })()
        campagne.ajouter_video(video)
    
    controller = TriKosmosController(model)
    
    window = QMainWindow()
    window.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    window.setGeometry(50, 50, 1400, 900)
    
    view = TriKosmosView(controller)
    window.setCentralWidget(view)
    
    window.show()
    print("✅ Page de tri lancée!")
    sys.exit(app.exec())