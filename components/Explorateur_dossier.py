# --- Imports standard ---
import os
import sys
import subprocess

# --- Imports PyQt6 : types et widgets nécessaires ---
from PyQt6.QtCore import Qt, QDir, QUrl, QModelIndex
from PyQt6.QtGui import QAction, QDesktopServices, QFileSystemModel  # QFileSystemModel est utilisé comme modèle système
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeView, QTableView, QToolBar, QLineEdit, QComboBox,
    QMessageBox, QStatusBar, QMenu
)

class WinLikeExplorer(QMainWindow):
    # Fenêtre principale “façon Explorateur Windows”
    def __init__(self, start_path: str | None = None):
        super().__init__()
        self.setWindowTitle("Explorateur")  # Titre de la fenêtre
        self.resize(1100, 680)  # Taille initiale

        # Historique de navigation (comme un navigateur : arrière/avant)
        self.history: list[str] = []
        self.history_index: int = -1
        self._navigating_from_history = False  # drapeau pour ne pas re-renseigner l’historique lors d’un retour/avant

        # -------- Barre d'outils (navigation + filtre + barre d’adresse)
        tb = QToolBar("Navigation")
        tb.setMovable(False)  # barre fixe
        self.addToolBar(tb)

        # Actions de navigation
        self.act_back = QAction("⟵", self)     # Retour
        self.act_forward = QAction("⟶", self)  # Avancer
        self.act_up = QAction("⬆", self)       # Remonter d’un dossier
        self.act_refresh = QAction("⟳", self)  # Rafraîchir

        # Connexions des actions aux méthodes
        self.act_back.triggered.connect(self.go_back)
        self.act_forward.triggered.connect(self.go_forward)
        self.act_up.triggered.connect(self.go_up)
        self.act_refresh.triggered.connect(self.refresh)

        # Ajout des actions à la barre d’outils
        tb.addAction(self.act_back)
        tb.addAction(self.act_forward)
        tb.addSeparator()
        tb.addAction(self.act_up)
        tb.addAction(self.act_refresh)
        tb.addSeparator()

        # Barre d’adresse : entrer un chemin à la main
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Chemin (ex: C:\\Users\\HP\\Documents)")
        self.path_edit.returnPressed.connect(self.on_path_entered)  # Entrée -> naviguer vers le chemin saisi
        tb.addWidget(self.path_edit)

        tb.addSeparator()

        # Filtre de type de fichiers (tous / vidéos)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Tous les fichiers", "Vidéos (*.mp4 *.avi *.mov *.mkv)"])
        self.filter_combo.currentIndexChanged.connect(self.apply_name_filters)  # changer le filtre
        tb.addWidget(self.filter_combo)

        # -------- Modèles & vues (liaison au système de fichiers)

        # Modèle pour l’arborescence de dossiers (volet gauche)
        self.dir_model = QFileSystemModel(self)
        self.dir_model.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Drives)  # dossiers/lecteurs, sans . et ..
        self.dir_model.setRootPath(QDir.rootPath())  # racine du système

        # Modèle pour le contenu d’un dossier (volet droit)
        self.file_model = QFileSystemModel(self)
        self.file_model.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllEntries)  # fichiers + dossiers
        self.file_model.setRootPath(QDir.rootPath())
        self.file_model.setNameFilterDisables(False)  # quand un filtre est actif, masquer les non-correspondants

        # Vue arborescente (gauche) des dossiers
        self.tree = QTreeView()
        self.tree.setModel(self.dir_model)
        self.tree.setHeaderHidden(False)
        self.tree.setColumnWidth(0, 260)
        self.tree.setAnimated(True)
        self.tree.setIndentation(18)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # clic droit custom
        self.tree.customContextMenuRequested.connect(self.show_dir_context_menu)
        self.tree.selectionModel().currentChanged.connect(self.on_tree_current_changed)  # sélection -> naviguer

        # Vue tabulaire (droite) des fichiers
        self.table = QTableView()
        self.table.setModel(self.file_model)
        self.table.setSortingEnabled(True)  # tri par colonnes
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)  # sélection par ligne
        self.table.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)  # sélection multiple possible
        self.table.doubleClicked.connect(self.on_table_double_clicked)  # double-clic -> ouvrir/entrer
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # clic droit custom
        self.table.customContextMenuRequested.connect(self.show_file_context_menu)
        # colonnes: 0=Nom, 1=Taille, 2=Type, 3=Modifié
        self.table.setColumnWidth(0, 420)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 160)
        self.table.setColumnWidth(3, 200)

        # Splitter pour séparer gauche/droite et permettre le redimensionnement
        splitter = QSplitter()
        splitter.addWidget(self.tree)
        splitter.addWidget(self.table)
        splitter.setStretchFactor(0, 1)  # proportion d’espace
        splitter.setStretchFactor(1, 2)

        # Conteneur central + layout vertical
        central = QWidget()
        lay = QVBoxLayout(central)
        lay.addWidget(splitter)
        self.setCentralWidget(central)

        # -------- Status bar (messages en bas)
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Dossier de départ : chemin reçu ou HOME par défaut
        start = start_path or QDir.homePath()
        self.navigate_to(start, add_to_history=True)  # naviguer et initialiser l’historique

        self.update_nav_actions()  # activer/désactiver boutons selon l’état
        self.apply_name_filters()  # appliquer le filtre initial (tous les fichiers)

    # ====== Navigation & historique
    def navigate_to(self, path: str, add_to_history: bool = True):
        # Fonction centrale de navigation : vérifie, met à jour vues + historique
        path = os.path.normpath(path)
        if not os.path.exists(path):
            QMessageBox.warning(self, "Chemin introuvable", f"Le chemin n'existe pas:\n{path}")
            return

        # Met à jour l’arborescence (sélectionner/faire défiler vers ce dossier)
        dir_index = self.dir_model.index(path)
        if dir_index.isValid():
            self.tree.setCurrentIndex(dir_index)
            self.tree.scrollTo(dir_index)

        # Met à jour la table (racine affichée = ce dossier)
        file_index = self.file_model.index(path)
        if file_index.isValid():
            self.table.setRootIndex(file_index)

        # Barre d’adresse + message de statut
        self.path_edit.setText(path)
        self.status.showMessage(path, 3000)

        # Enregistrer dans l’historique si navigation “normale”
        if add_to_history and not self._navigating_from_history:
            # Si on était revenu en arrière, couper la suite avant d’ajouter
            if self.history_index < len(self.history) - 1:
                self.history = self.history[: self.history_index + 1]
            self.history.append(path)
            self.history_index = len(self.history) - 1

        self.update_nav_actions()  # (dés)activer flèches

    def update_nav_actions(self):
        # Active/désactive les boutons en fonction de la position dans l’historique
        self.act_back.setEnabled(self.history_index > 0)
        self.act_forward.setEnabled(self.history_index >= 0 and self.history_index < len(self.history) - 1)
        # up possible si un parent existe
        self.act_up.setEnabled(True)

    def go_back(self):
        # Revenir en arrière dans l’historique
        if self.history_index > 0:
            self._navigating_from_history = True
            self.history_index -= 1
            self.navigate_to(self.history[self.history_index], add_to_history=False)
            self._navigating_from_history = False

    def go_forward(self):
        # Aller en avant dans l’historique
        if self.history_index < len(self.history) - 1:
            self._navigating_from_history = True
            self.history_index += 1
            self.navigate_to(self.history[self.history_index], add_to_history=False)
            self._navigating_from_history = False

    def go_up(self):
        # Remonter d’un dossier (parent)
        current = self.current_path()
        parent = os.path.dirname(current)
        if parent and parent != current:
            self.navigate_to(parent, add_to_history=True)

    def refresh(self):
        # Forcer un "reset" du modèle sur le répertoire courant (rafraîchir)
        current = self.current_path()
        self.dir_model.setRootPath("")  # astuce de reset
        self.dir_model.setRootPath(QDir.rootPath())
        self.file_model.setRootPath("")
        self.file_model.setRootPath(QDir.rootPath())
        self.navigate_to(current, add_to_history=False)

    def current_path(self) -> str:
        # Retourner le chemin actuellement affiché (priorité au volet droit)
        idx = self.table.rootIndex()
        if idx.isValid():
            return os.path.normpath(self.file_model.filePath(idx))
        # Sinon, prendre la sélection du volet gauche
        idx = self.tree.currentIndex()
        if idx.isValid():
            return os.path.normpath(self.dir_model.filePath(idx))
        # Sinon, HOME
        return os.path.normpath(QDir.homePath())

    # ====== Slots UI
    def on_path_entered(self):
        # Appuyé sur Entrée dans la barre d’adresse -> naviguer
        path = self.path_edit.text().strip().strip('"')
        if path:
            self.navigate_to(path, add_to_history=True)

    def on_tree_current_changed(self, current: QModelIndex, _prev: QModelIndex):
        # Sélection d’un dossier dans l’arborescence -> naviguer
        path = self.dir_model.filePath(current)
        if os.path.isdir(path):
            self.navigate_to(path, add_to_history=True)

    def on_table_double_clicked(self, index: QModelIndex):
        # Double-clic sur un élément du tableau -> entrer (dossier) ou ouvrir (fichier)
        path = self.file_model.filePath(index)
        if os.path.isdir(path):
            self.navigate_to(path, add_to_history=True)
        else:
            self.open_file(path)

    # ====== Filtres
    def apply_name_filters(self):
        # Appliquer le filtre choisi (tous les fichiers / extensions vidéo)
        mode = self.filter_combo.currentIndex()
        if mode == 0:
            self.file_model.setNameFilters([])  # aucun filtre -> tout afficher
        else:
            # vidéos courantes
            self.file_model.setNameFilters(["*.mp4", "*.avi", "*.mov", "*.mkv"])

    # ====== Actions fichiers / dossiers
    def open_file(self, path: str):
        # Ouvrir un fichier avec l’application par défaut du système
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]  # Windows
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))  # macOS / Linux
        except Exception as e:
            QMessageBox.critical(self, "Ouverture impossible", f"{path}\n\n{e}")

    def show_in_explorer(self, path: str):
        # Afficher le fichier/dossier dans l’explorateur système (sélectionné)
        try:
            if sys.platform.startswith("win"):
                # ouvrir l'explorateur et sélectionner l'élément
                subprocess.run(["explorer", "/select,", path])
            elif sys.platform == "darwin":
                subprocess.run(["open", "-R", path])
            else:
                folder = path if os.path.isdir(path) else os.path.dirname(path)
                subprocess.run(["xdg-open", folder])
        except Exception as e:
            QMessageBox.critical(self, "Action impossible", f"{path}\n\n{e}")

    # ====== Menus contextuels
    def show_file_context_menu(self, pos):
        # Menu clic droit dans le tableau de fichiers
        index = self.table.indexAt(pos)
        global_pos = self.table.viewport().mapToGlobal(pos)
        menu = QMenu(self)

        if index.isValid():
            # Clic sur un fichier/élément
            path = self.file_model.filePath(index)
            act_open = QAction("Ouvrir", self)
            act_open.triggered.connect(lambda: self.open_file(path))
            menu.addAction(act_open)

            act_show = QAction("Afficher dans l'Explorateur", self)
            act_show.triggered.connect(lambda: self.show_in_explorer(path))
            menu.addAction(act_show)
        else:
            # Clic dans le vide : actions sur le dossier courant
            cur = self.current_path()
            act_show_dir = QAction("Ouvrir le dossier courant dans l'Explorateur", self)
            act_show_dir.triggered.connect(lambda: self.show_in_explorer(cur))
            menu.addAction(act_show_dir)

        menu.exec(global_pos)

    def show_dir_context_menu(self, pos):
        # Menu clic droit dans l’arborescence des dossiers
        index = self.tree.indexAt(pos)
        global_pos = self.tree.viewport().mapToGlobal(pos)
        if not index.isValid():
            return
        path = self.dir_model.filePath(index)
        menu = QMenu(self)

        act_open = QAction("Ouvrir dans l'Explorateur", self)
        act_open.triggered.connect(lambda: self.show_in_explorer(path))
        menu.addAction(act_open)

        menu.exec(global_pos)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Démarrer dans Documents si dispo (HOME sinon)
    start = QDir.homePath()
    win = WinLikeExplorer(start_path=start)
    win.show()
    sys.exit(app.exec())
