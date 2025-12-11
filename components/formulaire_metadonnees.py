"""
Composant Formulaire Métadonnées
Gère l'affichage et l'édition des métadonnées (communes et propres)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QLineEdit, QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from models.app_model import METADATA_COMMUNES_LABELS, METADATA_PROPRES_LABELS

class FormulaireMetadonnees(QWidget):
    """
    Widget contenant les deux sections de métadonnées :
    - Communes (System, Campaign)
    - Propres (Video specific)
    """
    
    # Signaux émis vers la vue/contrôleur
    modification_communes_demandee = pyqtSignal(dict)
    modification_propres_demandee = pyqtSignal(dict)
    precalcul_demande = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.edit_communes = False
        self.edit_propres = False
        
        # Stockage des widgets d'édition
        self.meta_communes_fields = {}
        self.meta_propres_fields = {}
        
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout() # Utiliser un layout horizontal pour le splitter
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Section Communes
        self.communes_container = self.create_metadata_section("Métadonnées communes", type_meta="communes")
        splitter.addWidget(self.communes_container)
        
        # Section Propres
        self.propres_container = self.create_metadata_section("Métadonnées propres", type_meta="propres")
        splitter.addWidget(self.propres_container)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        self.setLayout(layout)

    def create_metadata_section(self, title, type_meta="communes"):
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
        
        # Zone de défilement
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
        
        btn_style_sheet = "QPushButton { background-color: transparent; color: white; border: 2px solid white; border-radius: 4px; font-size: 10px; font-weight: bold; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); } QPushButton:disabled { color: #555; border-color: #555; }"
        
        if type_meta == "communes":
            self.meta_communes_scroll_layout = scroll_layout
            
            self.btn_modifier_communes = QPushButton("Modifier")
            self.btn_modifier_communes.setFixedSize(90, 26)
            self.btn_modifier_communes.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_modifier_communes.setStyleSheet(btn_style_sheet)
            self.btn_modifier_communes.clicked.connect(self.on_toggle_edit_communes)
            self.btn_modifier_communes.setEnabled(False)

            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(self.btn_modifier_communes)
            btn_layout.setContentsMargins(0, 4, 0, 4)
            content_layout.addLayout(btn_layout)

        else:
            self.meta_propres_scroll_layout = scroll_layout
            
            self.btn_precalculer = QPushButton("Pré-calculer")
            self.btn_precalculer.setFixedSize(90, 26)
            self.btn_precalculer.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_precalculer.setStyleSheet(btn_style_sheet)
            self.btn_precalculer.clicked.connect(self.precalcul_demande.emit)
            self.btn_precalculer.setEnabled(False)
            
            self.btn_modifier_propres = QPushButton("Modifier")
            self.btn_modifier_propres.setFixedSize(90, 26)
            self.btn_modifier_propres.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_modifier_propres.setStyleSheet(btn_style_sheet)
            self.btn_modifier_propres.clicked.connect(self.on_toggle_edit_propres)
            self.btn_modifier_propres.setEnabled(False) 
            
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(self.btn_precalculer)
            btn_layout.addWidget(self.btn_modifier_propres)
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

    def vider_layout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                elif child.layout():
                    self.vider_layout(child.layout())

    def remplir_communes(self, sections: dict):
        """
        Remplit la section des métadonnées communes.
        Attend un dictionnaire structuré par sections (ex: {'system': {...}, 'campaign': {...}})
        """
        self.vider_layout(self.meta_communes_scroll_layout)
        self.meta_communes_fields.clear()
        
        ordered_sections = ['system', 'campaign']
        
        for section_name in ordered_sections:
            if section_name not in sections: continue
            
            section_label = QLabel(f"{section_name.upper()}")
            section_label.setStyleSheet("color: white; font-weight: bold; font-size: 11px; padding: 5px 0px 2px 0px;")
            self.meta_communes_scroll_layout.addWidget(section_label)
            
            for full_key, value in sections[section_name].items():
                display_label = METADATA_COMMUNES_LABELS.get(full_key, full_key)
                row = self.create_metadata_row(display_label, readonly=True)
                row['widget'].setText(str(value))
                self.meta_communes_fields[full_key] = row['widget']
                self.meta_communes_scroll_layout.addWidget(row['container'])
        
        self.btn_modifier_communes.setEnabled(True)
        self.reset_edit_communes()

    def remplir_propres(self, sections: dict):
        """
        Remplit la section des métadonnées propres.
        Attend un dictionnaire structuré par sections.
        """
        self.vider_layout(self.meta_propres_scroll_layout)
        self.meta_propres_fields.clear()
        
        ordered_sections = ['stationDict', 'hourDict', 'gpsDict', 'meteoAirDict', 'meteoMerDict', 'astroDict', 'ctdDict', 'analyseDict', 'general']

        for section_name in ordered_sections:
            if section_name not in sections: continue
            fields = sections[section_name]
            if not fields: continue
                
            section_label = QLabel(f"{section_name.replace('Dict', '').upper()}")
            section_label.setStyleSheet("color: white; font-weight: bold; font-size: 11px; padding: 5px 0px 2px 0px;")
            self.meta_propres_scroll_layout.addWidget(section_label)
            
            sorted_fields = sorted(fields.items(), key=lambda item: item[0])

            for field_name, (full_key, value) in sorted_fields:
                display_label = METADATA_PROPRES_LABELS.get(field_name, field_name)
                row = self.create_metadata_row(display_label, readonly=True)
                
                if value in ["None", "null", "N/A (API)"]:
                    row['widget'].setText("")
                else:
                    row['widget'].setText(str(value))
                
                self.meta_propres_fields[full_key] = row['widget']
                self.meta_propres_scroll_layout.addWidget(row['container'])
        
        self.btn_modifier_propres.setEnabled(True)
        self.btn_precalculer.setEnabled(True)
        self.reset_edit_propres()

    def on_toggle_edit_communes(self):
        if not self.edit_communes:
            # Passer en mode édition
            for w in self.meta_communes_fields.values(): w.setReadOnly(False)
            self.edit_communes = True
            self.btn_modifier_communes.setText("OK")
            self.btn_modifier_propres.setEnabled(False) # Bloquer l'autre
        else:
            # Valider et émettre
            nouvelles_meta = {k: w.text() for k, w in self.meta_communes_fields.items()}
            self.modification_communes_demandee.emit(nouvelles_meta)
            # Le reset se fera si succès via appel externe ou on peut le faire ici
            # Pour l'instant on attend que le contrôleur confirme, mais pour simplifier l'UI :
            # On laisse le contrôleur appeler reset_edit_communes() en cas de succès

    def on_toggle_edit_propres(self):
        if not self.edit_propres:
            for w in self.meta_propres_fields.values(): w.setReadOnly(False)
            self.edit_propres = True
            self.btn_modifier_propres.setText("OK")
            self.btn_precalculer.setEnabled(False)
            self.btn_modifier_communes.setEnabled(False)
        else:
            nouvelles_meta = {k: w.text() for k, w in self.meta_propres_fields.items()}
            self.modification_propres_demandee.emit(nouvelles_meta)

    def reset_edit_communes(self):
        for w in self.meta_communes_fields.values(): w.setReadOnly(True)
        self.edit_communes = False
        self.btn_modifier_communes.setText("Modifier")
        self.btn_modifier_propres.setEnabled(True)

    def reset_edit_propres(self):
        for w in self.meta_propres_fields.values(): w.setReadOnly(True)
        self.edit_propres = False
        self.btn_modifier_propres.setText("Modifier")
        self.btn_precalculer.setEnabled(True)
        self.btn_modifier_communes.setEnabled(True)
    
    def set_precalcul_loading(self, loading=True):
        if loading:
            self.btn_precalculer.setText("Calcul...")
            self.btn_precalculer.setEnabled(False)
            self.btn_modifier_propres.setEnabled(False)
        else:
            self.btn_precalculer.setText("Pré-calculer")
            self.btn_precalculer.setEnabled(True)
            self.btn_modifier_propres.setEnabled(True)
