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
    QGridLayout, QLineEdit, QMenu, QMessageBox, QDialog, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QThread, QTimer, QEvent
from PyQt6.QtGui import QFont, QAction, QPalette, QColor, QPixmap, QMovie

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
# CLASSE WIDGET MINIATURE ANIMÉE (Code branche romain)
# ═══════════════════════════════════════════════════════════════

class AnimatedThumbnailLabel(QLabel):
    """
    QLabel personnalisé qui gère l'affichage d'un Pixmap statique
    et le remplace par un QMovie animé lors du survol.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.static_pixmap = None
        self.animated_movie = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #2a2a2a; border: 1px solid #555; color: #888;")
        self.setText("🔄")  # Symbole de chargement initial
    
    def set_static_pixmap(self, pixmap):
        """Définit l'image statique (miniature)"""
        self.static_pixmap = pixmap
        if self.movie() is None:
            self.setPixmap(self.static_pixmap)
            self.setText("")
    
    def set_animated_movie(self, movie):
        """Stocke le GIF animé pour une utilisation future"""
        self.animated_movie = movie
        if self.animated_movie:
            self.animated_movie.setCacheMode(QMovie.CacheMode.CacheAll)
    
    def enterEvent(self, event):
        """Souris entre : joue le GIF"""
        if self.animated_movie:
            self.setMovie(self.animated_movie)
            self.animated_movie.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Souris sort : arrête le GIF et remet l'image statique"""
        if self.animated_movie:
            self.animated_movie.stop()
        
        # Correction anti-plantage (TypeNone)
        if self.static_pixmap:
            self.setPixmap(self.static_pixmap)
        else:
            self.setPixmap(QPixmap())
            self.setText("🔄")
        
        super().leaveEvent(event)


# ═══════════════════════════════════════════════════════════════
# EXTRACTION DE MINIATURES (THREAD) (Code branche romain)
# ═══════════════════════════════════════════════════════════════

class PreviewExtractorThread(QThread):
    """
    Thread pour extraire une miniature STATIQUE et un GIF ANIMÉ
    """
    thumbnail_ready = pyqtSignal(int, QPixmap)
    # Émet un 'str' (chemin du GIF) au lieu d'un QMovie
    gif_ready = pyqtSignal(int, str)
    
    def __init__(self, video_path, seek_info: list, parent=None):
        """
        seek_info est une liste de tuples: [(start_time_str, duration_sec), ...]
        """
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
                
                gif_path = self.temp_dir / f"gif_{Path(self.video_path).stem}_{idx}_{safe_seek_time}.gif"
                movie_success = self.extract_gif(seek_time, duration, gif_path)
                if movie_success and self._is_running:
                    self.gif_ready.emit(idx, str(gif_path))

            except Exception as e:
                print(f"⚠️ Erreur extraction preview {idx}: {e}")

    def extract_thumbnail(self, seek_time, output_path):
        if output_path.exists():
            pixmap = QPixmap(str(output_path))
            if not pixmap.isNull():
                return pixmap
        
        cmd = [
            'ffmpeg', '-ss', seek_time, '-i', self.video_path,
            '-vframes', '1', '-vf', 'scale=320:-1', 
            '-q:v', '3', '-y', str(output_path)
        ]
        try:
            result = subprocess.run(cmd, 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.PIPE, 
                                    timeout=5, 
                                    text=True, 
                                    encoding='utf-8')
            if result.returncode != 0:
                print(f"❌ Erreur FFmpeg (thumb) - Commande: {' '.join(cmd)}")
                print(f"   Erreur: {result.stderr}")

            if output_path.exists():
                return QPixmap(str(output_path))
        except FileNotFoundError:
             print("❌ ERREUR CRITIQUE : ffmpeg n'est pas trouvé. Vérifiez votre PATH système.")
             self.stop()
        except Exception as e:
            print(f"Erreur Python (thumb): {e}")
        return None

    def extract_gif(self, seek_time, duration: int, output_path) -> bool:
        if output_path.exists():
            temp_movie = QMovie(str(output_path))
            if temp_movie.isValid():
                return True
        
        # Filtre vidéo : fps=10, scale=320px, et setpts=0.5*PTS (accélération x2)
        video_filter = f'fps=10,scale=320:-1:flags=lanczos,setpts=0.5*PTS'
        
        cmd = [
            'ffmpeg',
            '-ss', seek_time,
            '-t', str(duration),
            '-i', self.video_path,
            '-vf', video_filter,
            '-y',
            str(output_path)
        ]
        try:
            result = subprocess.run(cmd, 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.PIPE, 
                                    timeout=15, 
                                    text=True, 
                                    encoding='utf-8')
            if result.returncode != 0:
                print(f"❌ Erreur FFmpeg (gif) - Commande: {' '.join(cmd)}")
                print(f"   Erreur: {result.stderr}")
                return False
            
            if output_path.exists():
                return True
        except FileNotFoundError:
             print("❌ ERREUR CRITIQUE : ffmpeg n'est pas trouvé. Vérifiez votre PATH système.")
             self.stop()
        except Exception as e:
            print(f"Erreur Python (gif): {e}")
        return False


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
        self.preview_extractor = None 
        self.current_seek_info = []
        # État d'édition pour les métadonnées propres (toggle lecture/écriture)
        self.edit_propres = False
        
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
        
        # APERÇU DES ANGLES (Code branche romain)
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
        for row in range(2):
            for col in range(3):
                thumb = AnimatedThumbnailLabel() 
                thumb.setMinimumSize(180, 100)
                thumb.setMaximumSize(280, 160)
                thumb.setScaledContents(True) 
                thumbnails_layout.addWidget(thumb, row, col)
                self.thumbnails.append(thumb)
        
        for i in range(2):
            thumbnails_layout.setRowStretch(i, 1)
        for i in range(3):
            thumbnails_layout.setColumnStretch(i, 1)
        
        thumbnails_widget.setLayout(thumbnails_layout)
        apercu_layout.addWidget(thumbnails_widget)
        apercu_container.setLayout(apercu_layout)
        
        layout.addWidget(apercu_container, stretch=1)
        
        # MÉTADONNÉES - DEUX SECTIONS
        meta_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Métadonnées communes (lecture seule)
        meta_communes_widget = self.create_metadata_section("Métadonnées communes", readonly=True, type_meta="communes")
        meta_splitter.addWidget(meta_communes_widget)
        
        # Métadonnées propres (modification possible)
        meta_propres_widget = self.create_metadata_section("Métadonnées propres", readonly=True, type_meta="propres")
        meta_splitter.addWidget(meta_propres_widget)
        
        # Forcer les deux sections à avoir exactement la même taille
        meta_splitter.setStretchFactor(0, 1)
        meta_splitter.setStretchFactor(1, 1)
        meta_splitter.setSizes([400, 400])  # Taille égale pour les deux panels
        
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
                # Créer les champs en mode lecture seule pour les métadonnées communes
                row = self.create_metadata_row(key, readonly=readonly)
                self.meta_communes_fields[key] = row['widget']
                content_layout.addWidget(row['container'])
            
            content_layout.addStretch()
            
            # Bouton "Modifier" décoratif pour les métadonnées communes (sans action)
            btn_modifier_communes = QPushButton("Modifier")
            btn_modifier_communes.setFixedSize(90, 26)
            btn_modifier_communes.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_modifier_communes.setStyleSheet("QPushButton { background-color: transparent; color: white; border: 2px solid white; border-radius: 4px; font-size: 10px; font-weight: bold; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }")
            
            
            btn_communes_layout = QHBoxLayout()
            btn_communes_layout.addStretch()
            btn_communes_layout.addWidget(btn_modifier_communes)
            btn_communes_layout.setContentsMargins(0, 4, 0, 4)
            content_layout.addLayout(btn_communes_layout)
            
        else:
            self.meta_propres_fields = {}
            self.meta_propres_widgets = {}
            
            # Créer un conteneur scrollable pour toutes les métadonnées propres
            self.meta_propres_scroll_area = QScrollArea()
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout()
            scroll_layout.setContentsMargins(5, 5, 5, 5)
            scroll_layout.setSpacing(3)
            
            # Stocker le layout pour pouvoir y ajouter dynamiquement des champs
            self.meta_propres_scroll_layout = scroll_layout
            
            scroll_widget.setLayout(scroll_layout)
            self.meta_propres_scroll_area.setWidget(scroll_widget)
            self.meta_propres_scroll_area.setWidgetResizable(True)
            self.meta_propres_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.meta_propres_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.meta_propres_scroll_area.setStyleSheet("QScrollArea { border: none; background-color: black; }")
            
            content_layout.addWidget(self.meta_propres_scroll_area)
            
            # Supprimer addStretch() pour que le scroll_area prenne tout l'espace
            
            btn_modifier = QPushButton("Modifier")
            btn_modifier.setFixedSize(90, 26)
            btn_modifier.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_modifier.setStyleSheet("QPushButton { background-color: transparent; color: white; border: 2px solid white; border-radius: 4px; font-size: 10px; font-weight: bold; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }")
            btn_modifier.clicked.connect(self.on_modifier_metadata_propres)
            # Commencer désactivé jusqu'à sélection d'une vidéo
            btn_modifier.setEnabled(False)
            # Conserve une référence au bouton pour changer le libellé entre "Modifier" et "Sauvegarder"
            self.btn_modifier_propres = btn_modifier
            
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(btn_modifier)
            btn_layout.setContentsMargins(0, 4, 0, 4)
            content_layout.addLayout(btn_layout)
        
        content_widget.setLayout(content_layout)
        layout.addWidget(content_widget)
        container.setLayout(layout)
        
        return container
    
    # Création d'une ligne de métadonnée avec support lecture/édition
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
        value_widget.setReadOnly(readonly)  # important pour mode lecture/édition
        value_widget.setStyleSheet("color: white; padding: 3px; background-color: #1a1a1a; border: 1px solid #555; font-size: 10px;")
        
        row_layout.addWidget(value_widget)
        row_widget.setLayout(row_layout)
        
        return {'container': row_widget, 'widget': value_widget}
    
    def remplir_metadonnees_propres(self, metadata_propres: dict):
        """Remplit dynamiquement la section des métadonnées propres"""
        # Vider le layout existant
        self.vider_layout(self.meta_propres_scroll_layout)
        self.meta_propres_fields.clear()
        self.meta_propres_widgets.clear()
        
        # Organiser les métadonnées par section
        sections = {}
        for key, value in metadata_propres.items():
            if '_' in key:
                section_name, field_name = key.split('_', 1)
                if section_name not in sections:
                    sections[section_name] = {}
                sections[section_name][field_name] = value
            else:
                if 'general' not in sections:
                    sections['general'] = {}
                sections['general'][key] = value
        
        # Créer des sections organisées
        for section_name, fields in sections.items():
            if not fields:  # Skip empty sections
                continue
                
            # Titre de section
            section_label = QLabel(f"{section_name.upper()}")
            section_label.setStyleSheet("color: white; font-weight: bold; font-size: 11px; padding: 5px 0px 2px 0px;")
            self.meta_propres_scroll_layout.addWidget(section_label)
            
            # Champs de la section
            for field_name, value in fields.items():
                full_key = f"{section_name}_{field_name}" if section_name != 'general' else field_name
                row = self.create_metadata_row(field_name, readonly=True)
                row['widget'].setText(str(value))
                
                self.meta_propres_fields[full_key] = row['widget']
                self.meta_propres_widgets[full_key] = row['container']
                self.meta_propres_scroll_layout.addWidget(row['container'])
        
        # Ne pas ajouter de stretch pour utiliser tout l'espace disponible
    
    def vider_layout(self, layout):
        """Vide complètement un layout"""
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
        """Charge uniquement la liste des vidéos, sans miniatures"""
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
    

    
    def lancer_extraction_previews(self, video_path, seek_info):
        """Lance l'extraction des 6 miniatures ET GIFs en arrière-plan."""
        
        if self.preview_extractor and self.preview_extractor.isRunning():
            self.preview_extractor.stop()
            self.preview_extractor.wait()
        
        for thumb in self.thumbnails:
            thumb.setText("🔄")
            thumb.setPixmap(QPixmap())
            thumb.setMovie(None)
            thumb.set_animated_movie(None)
            thumb.static_pixmap = None

        print(f"🎬 Lancement extraction previews pour {video_path}...")
        
        self.preview_extractor = PreviewExtractorThread(video_path, seek_info)
        
        self.preview_extractor.thumbnail_ready.connect(self.afficher_miniature)
        self.preview_extractor.gif_ready.connect(self.stocker_gif_preview)
        
        self.preview_extractor.start()

    def afficher_miniature(self, index, pixmap):
        """Slot : Affiche une miniature statique extraite."""
        if index < len(self.thumbnails):
            self.thumbnails[index].set_static_pixmap(pixmap)
            print(f"✅ Miniature statique {index+1} affichée")
    
    def stocker_gif_preview(self, index, gif_path: str):
        """Slot : Crée et stocke le QMovie animé à partir du chemin du GIF."""
        if index < len(self.thumbnails):
            movie = QMovie(gif_path)
            if movie.isValid():
                self.thumbnails[index].set_animated_movie(movie)
                print(f"✅ GIF animé {index+1} stocké")
            else:
                print(f"⚠️ GIF invalide reçu : {gif_path}")
    
    def on_video_selected(self):
        selected = self.table.selectedItems()
        if selected and self.controller:
            row = selected[0].row()
            nom_video = self.table.item(row, 0).text()
            self.controller.selectionner_video(nom_video)
    
    def afficher_video(self, video):
        """Slot : Met à jour toute la partie droite lors de la sélection"""
        self.video_selectionnee = video
        
        print(f"\n📹 Vidéo sélectionnée : {video.nom}")
        
        # Charger les métadonnées depuis le JSON via le contrôleur
        if self.controller:
            self.controller.charger_metadonnees_depuis_json(video)
            # Charger aussi les métadonnées communes depuis le JSON
            self.controller.charger_metadonnees_communes_depuis_json(video)
        
        print(f"   Métadonnées communes : {video.metadata_communes}")
        print(f"   Métadonnées propres : {video.metadata_propres}")
        
        # Métadonnées communes (affichage lecture seule)
        self.meta_communes_fields['system'].setText(video.metadata_communes.get('system', ''))
        self.meta_communes_fields['camera'].setText(video.metadata_communes.get('camera', ''))
        self.meta_communes_fields['model'].setText(video.metadata_communes.get('model', ''))
        self.meta_communes_fields['version'].setText(video.metadata_communes.get('version', ''))
        
        # Métadonnées propres (afficher TOUTES dynamiquement)
        self.remplir_metadonnees_propres(video.metadata_propres)
        
        # Activer le bouton "Modifier" maintenant qu'une vidéo est sélectionnée
        if hasattr(self, "btn_modifier_propres") and self.btn_modifier_propres:
            self.btn_modifier_propres.setEnabled(True)
        
        # Lancer l'extraction des 6 miniatures/GIFs (avec gestion d'erreur FFmpeg)
        if self.controller:
            self.current_seek_info = self.controller.get_angle_seek_times(video.nom)
            try:
                self.lancer_extraction_previews(video.chemin, self.current_seek_info)
            except Exception as e:
                print("⚠️ Aperçus vidéo non disponibles (FFmpeg requis)")
                # Les métadonnées fonctionnent sans les aperçus !
    
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
    

    
    # Bouton "Modifier" pour métadonnées propres - bascule entre édition et sauvegarde
    def on_modifier_metadata_propres(self):
        if not (self.video_selectionnee and self.controller):
            return

        # Si pas encore en édition → activer l’édition
        if not self.edit_propres:
            for w in self.meta_propres_fields.values():
                w.setReadOnly(False)
            self.edit_propres = True
            # changer le libellé du bouton à "Enregistrer"
            if hasattr(self, "btn_modifier_propres") and self.btn_modifier_propres:
                
                self.btn_modifier_propres.setText("OK")
                self.btn_modifier_propres.setStyleSheet("QPushButton { background-color: transparent; color: white; border: 2px solid white; border-radius: 4px; font-size: 10px; font-weight: bold; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }")
            return

        # Déjà en édition → sauvegarder toutes les métadonnées propres
        if not self.video_selectionnee:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Aucune vidéo sélectionnée", "Veuillez sélectionner une vidéo avant de valider.")
            return

        # Collecter les métadonnées des champs
        nouvelles_meta = {}
        for key, widget in self.meta_propres_fields.items():
            nouvelles_meta[key] = widget.text()
        
        # Sauvegarder via le contrôleur
        ok = self.controller.modifier_metadonnees_propres(self.video_selectionnee.nom, nouvelles_meta)

        if ok:
            # Afficher le message de succès
            self.controller.show_success_dialog(self)
            
            # repasser en lecture seule
            for w in self.meta_propres_fields.values():
                w.setReadOnly(True)
            self.edit_propres = False
            if hasattr(self, "btn_modifier_propres") and self.btn_modifier_propres:
                self.btn_modifier_propres.setText("Modifier")
                self.btn_modifier_propres.setStyleSheet("QPushButton { background-color: transparent; color: white; border: 2px solid white; border-radius: 4px; font-size: 10px; font-weight: bold; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }")
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Impossible de sauvegarder les métadonnées dans le fichier JSON")


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
    
    controller = TriKosmosController(model)
    
    window = QMainWindow()
    window.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    window.setGeometry(50, 50, 1400, 900)
    
    view = TriKosmosView(controller)
    window.setCentralWidget(view)
    
    window.show()
    print("✅ Page de tri lancée!")
    sys.exit(app.exec())
