"""
VUE - Page de tri KOSMOS
Architecture MVC - Vue uniquement
"""
import sys
import os
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QSplitter,
    QGridLayout, QLineEdit, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QThread
from PyQt6.QtGui import QFont, QAction, QPalette, QColor, QPixmap

# Import du contrôleur
from controllers.tri_controller import TriKosmosController

# ═══════════════════════════════════════════════════════════════
# EXTRACTION DE MINIATURES (THREAD)
# ═══════════════════════════════════════════════════════════════

class ThumbnailExtractor(QThread):
    """Thread pour extraire les miniatures des vidéos"""
    thumbnail_ready = pyqtSignal(int, QPixmap)  # index, pixmap
    
    def __init__(self, videos, parent=None):
        super().__init__(parent)
        self.videos = videos[:6]  # Maximum 6 miniatures
        
    def run(self):
        """Extrait les miniatures"""
        for idx, video in enumerate(self.videos):
            try:
                pixmap = self.extract_thumbnail(video.chemin)
                if pixmap:
                    self.thumbnail_ready.emit(idx, pixmap)
            except Exception as e:
                print(f"⚠️ Erreur extraction miniature {video.nom}: {e}")
    
    def extract_thumbnail(self, video_path):
        """Extrait une miniature d'une vidéo avec ffmpeg"""
        if not os.path.exists(video_path):
            print(f"⚠️ Fichier vidéo non trouvé: {video_path}")
            return None
        
        try:
            # Créer un dossier temporaire
            temp_dir = Path(video_path).parent / ".thumbnails"
            temp_dir.mkdir(exist_ok=True)
            
            # Nom du fichier de sortie
            thumbnail_path = temp_dir / f"thumb_{Path(video_path).stem}.jpg"
            
            # Si la miniature existe déjà, la charger
            if thumbnail_path.exists():
                pixmap = QPixmap(str(thumbnail_path))
                if not pixmap.isNull():
                    return pixmap
            
            # Commande ffmpeg pour extraire une frame à 1 seconde
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', '00:00:01',
                '-vframes', '1',
                '-vf', 'scale=320:-1',
                '-y',
                str(thumbnail_path)
            ]
            
            # Exécuter ffmpeg
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            
            if result.returncode == 0 and thumbnail_path.exists():
                # Charger l'image
                pixmap = QPixmap(str(thumbnail_path))
                return pixmap
            
        except subprocess.TimeoutExpired:
            print(f"⚠️ Timeout extraction miniature")
        except FileNotFoundError:
            print(f"⚠️ ffmpeg non trouvé, miniatures désactivées")
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
# CONTRÔLEUR
# ═══════════════════════════════════════════════════════════════



# ═══════════════════════════════════════════════════════════════
# VUE
# ═══════════════════════════════════════════════════════════════

class TriKosmosView(QWidget):
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.video_selectionnee = None
        self.thumbnail_extractor = None
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
            QTableWidget {
                background-color: black;
                color: white;
                border: 2px solid white;
                gridline-color: #555;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #333;
            }
            QTableWidget::item:selected {
                background-color: #1DA1FF;
            }
            QHeaderView::section {
                background-color: white;
                color: black;
                padding: 6px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        layout.addWidget(self.table)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(6)
        buttons_layout.setContentsMargins(5, 5, 5, 5)
        
        for btn_text, callback in [
            ("Renommer", self.on_renommer),
            ("Conserver", self.on_conserver),
            ("Supprimer", self.on_supprimer)
        ]:
            btn = QPushButton(btn_text)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    border: 2px solid white;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
            """)
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
        
        # APERÇU
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
                thumb = QLabel()
                thumb.setMinimumSize(180, 100)
                thumb.setMaximumSize(280, 160)
                thumb.setStyleSheet("background-color: #2a2a2a; border: 1px solid #555; color: #888;")
                thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
                thumb.setText("📹")
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
        container.setStyleSheet("""
        #metadata_section {
            background-color: black; border: 2px solid white;
        }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # TITRE AVEC PADDING RÉDUIT
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
            # MÉTADONNÉES COMMUNES
            self.meta_communes_fields = {}
            for key in ['System', 'camera', 'Model', 'System ', 'Version']:
                row = self.create_metadata_row(key, readonly=False)
                self.meta_communes_fields[key] = row['widget']
                content_layout.addWidget(row['container'])
            
            content_layout.addStretch()
            
            # BOUTON MODIFIER pour communes
            btn_modifier_communes = QPushButton("Modifier")
            btn_modifier_communes.setFixedSize(90, 26)
            btn_modifier_communes.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_modifier_communes.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    border: 2px solid white;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
            """)
            btn_modifier_communes.clicked.connect(self.on_modifier_metadata_communes)
            
            btn_layout_c = QHBoxLayout()
            btn_layout_c.addStretch()
            btn_layout_c.addWidget(btn_modifier_communes)
            btn_layout_c.setContentsMargins(0, 4, 0, 4)
            content_layout.addLayout(btn_layout_c)
            
        else:
            # MÉTADONNÉES PROPRES
            self.meta_propres_fields = {}
            self.meta_propres_widgets = {}
            
            for key in ['Campaign', 'ZoneDict', 'Zone']:
                row = self.create_metadata_row(key, readonly=False)
                self.meta_propres_fields[key] = row['widget']
                self.meta_propres_widgets[key] = row['container']
                content_layout.addWidget(row['container'])
            
            content_layout.addStretch()
            
            # BOUTON MODIFIER pour propres
            btn_modifier = QPushButton("Modifier")
            btn_modifier.setFixedSize(90, 26)
            btn_modifier.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_modifier.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    border: 2px solid white;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
            """)
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
        label.setFixedWidth(55)
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
        
        # Lancer l'extraction des miniatures
        self.extraire_miniatures(videos)
    
    def extraire_miniatures(self, videos):
        """Lance l'extraction des miniatures en arrière-plan"""
        if len(videos) == 0:
            print("⚠️ Aucune vidéo à extraire")
            return
        
        if self.thumbnail_extractor and self.thumbnail_extractor.isRunning():
            self.thumbnail_extractor.terminate()
        
        self.thumbnail_extractor = ThumbnailExtractor(videos)
        self.thumbnail_extractor.thumbnail_ready.connect(self.afficher_miniature)
        self.thumbnail_extractor.start()
        
        print(f"🎬 Extraction de {min(6, len(videos))} miniatures lancée...")
    
    def afficher_miniature(self, index, pixmap):
        """Affiche une miniature extraite"""
        if index < len(self.thumbnails):
            self.thumbnails[index].setPixmap(pixmap)
            self.thumbnails[index].setText("")
            print(f"✅ Miniature {index+1} affichée")
    
    def on_video_selected(self):
        selected = self.table.selectedItems()
        if selected and self.controller:
            row = selected[0].row()
            nom_video = self.table.item(row, 0).text()
            self.controller.selectionner_video(nom_video)
    
    def afficher_video(self, video):
        self.video_selectionnee = video
        
        print(f"\n📹 Vidéo sélectionnée : {video.nom}")
        print(f"   Métadonnées communes : {video.metadata_communes}")
        print(f"   Métadonnées propres : {video.metadata_propres}")
        
        # Métadonnées communes
        self.meta_communes_fields['System'].setText(video.metadata_communes.get('system', ''))
        self.meta_communes_fields['camera'].setText(video.metadata_communes.get('camera', ''))
        self.meta_communes_fields['Model'].setText(video.metadata_communes.get('model', ''))
        self.meta_communes_fields['Version'].setText(video.metadata_communes.get('version', ''))
        
        # Métadonnées propres
        self.meta_propres_fields['Campaign'].setText(video.metadata_propres.get('campaign', ''))
        self.meta_propres_fields['ZoneDict'].setText(video.metadata_propres.get('zone_dict', ''))
        self.meta_propres_fields['Zone'].setText(video.metadata_propres.get('zone', ''))
    
    def on_renommer(self):
        print("🔄 Renommer vidéo")
    
    def on_conserver(self):
        if self.video_selectionnee and self.controller:
            self.controller.conserver_video(self.video_selectionnee.nom)
            print(f"✅ Vidéo conservée : {self.video_selectionnee.nom}")
    
    def on_supprimer(self):
        if self.video_selectionnee and self.controller:
            self.controller.supprimer_video(self.video_selectionnee.nom)
            print(f"🗑️ Vidéo marquée pour suppression : {self.video_selectionnee.nom}")
    
    def on_modifier_metadata_communes(self):
        if self.video_selectionnee and self.controller:
            nouvelles_meta = {
                'system': self.meta_communes_fields['System'].text(),
                'camera': self.meta_communes_fields['camera'].text(),
                'model': self.meta_communes_fields['Model'].text(),
                'version': self.meta_communes_fields['Version'].text()
            }
            
            if self.controller.modifier_metadonnees_communes(self.video_selectionnee.nom, nouvelles_meta):
                QMessageBox.information(self, "Succès", "Métadonnées communes modifiées et sauvegardées!")
                print(f"✅ Métadonnées communes sauvegardées")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de sauvegarder les métadonnées")
    
    def on_modifier_metadata_propres(self):
        if self.video_selectionnee and self.controller:
            nouvelles_meta = {
                'campaign': self.meta_propres_fields['Campaign'].text(),
                'zone_dict': self.meta_propres_fields['ZoneDict'].text(),
                'zone': self.meta_propres_fields['Zone'].text()
            }
            
            if self.controller.modifier_metadonnees_propres(self.video_selectionnee.nom, nouvelles_meta):
                QMessageBox.information(self, "Succès", "Métadonnées propres modifiées et sauvegardées!")
                print(f"✅ Métadonnées propres sauvegardées")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de sauvegarder les métadonnées")


# TEST
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow
    from datetime import datetime
    
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from app_model import ApplicationModel
    except ImportError:
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