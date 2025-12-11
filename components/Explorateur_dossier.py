"""
Composant Liste des Vidéos
Tableau affichant la liste des vidéos avec options de renommage et suppression.
Remplace l'ancien Explorateur_dossier.py pour la vue de Tri.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal

class VideoList(QWidget):
    """
    Widget affichant la liste des vidéos dans un tableau.
    Émet des signaux pour la sélection, le renommage et la suppression.
    """
    
    video_selected = pyqtSignal(str)  # Émet le nom de la vidéo
    rename_requested = pyqtSignal()   # Demande de renommage
    delete_requested = pyqtSignal()   # Demande de suppression
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Tableau des vidéos
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Noms", "Taille", "Durée", "Date"])
        
        # Configuration des colonnes
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(3, 90)
        
        # Comportement de sélection
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Style
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
        
        # Connexion du signal de sélection
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.table)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(6)
        buttons_layout.setContentsMargins(5, 5, 5, 5)
        
        self.btn_rename = QPushButton("Renommer")
        self.btn_rename.setFixedHeight(32)
        self.btn_rename.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_rename.setStyleSheet(self.get_button_style())
        self.btn_rename.clicked.connect(self.rename_requested.emit)
        buttons_layout.addWidget(self.btn_rename)
        
        self.btn_delete = QPushButton("Supprimer")
        self.btn_delete.setFixedHeight(32)
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setStyleSheet(self.get_button_style())
        self.btn_delete.clicked.connect(self.delete_requested.emit)
        buttons_layout.addWidget(self.btn_delete)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
        # Style du widget conteneur
        self.setStyleSheet("background-color: black;")

    def get_button_style(self):
        return """
            QPushButton { 
                background-color: black; 
                color: white; 
                border: 2px solid white; 
                border-radius: 4px; 
                font-size: 11px; 
                font-weight: bold; 
            } 
            QPushButton:hover { 
                background-color: #333333; 
            }
        """

    def update_video_list(self, videos):
        """Met à jour la liste des vidéos affichées."""
        self.table.setRowCount(len(videos))
        self.table.blockSignals(True) # Éviter de déclencher selectionChanged pendant le remplissage
        
        for row, video in enumerate(videos):
            self.table.setItem(row, 0, QTableWidgetItem(video.nom))
            self.table.setItem(row, 1, QTableWidgetItem(video.taille))
            self.table.setItem(row, 2, QTableWidgetItem(video.duree))
            self.table.setItem(row, 3, QTableWidgetItem(video.date))
            
        self.table.blockSignals(False)

    def select_video(self, video_name):
        """Sélectionne une vidéo par son nom."""
        items = self.table.findItems(video_name, Qt.MatchFlag.MatchExactly)
        if items:
            row = items[0].row()
            self.table.selectRow(row)

    def select_first_row(self):
        """Sélectionne la première ligne si elle existe."""
        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    def get_selected_video_name(self):
        """Retourne le nom de la vidéo sélectionnée ou None."""
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            return self.table.item(row, 0).text()
        return None

    def on_selection_changed(self):
        """Gère le changement de sélection interne."""
        name = self.get_selected_video_name()
        if name:
            self.video_selected.emit(name)

