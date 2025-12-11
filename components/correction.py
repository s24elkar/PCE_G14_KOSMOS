"""
Composant Correction des Images
Contrôles pour correction couleurs, contraste, luminosité et filtres avancés
"""
from typing import Optional 
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
                             QPushButton, QGroupBox, QGridLayout, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal


class ColorCorrectionButton(QPushButton):
    """Bouton de correction couleurs avec icône colorée"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        self.setText("🎨   Correction couleurs")
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: black;
                color: white;
                border: 2px solid white;
                border-radius: 8px;
                padding: 8px 12px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
                border-color: #2196F3;
            }
            QPushButton:pressed {
                background-color: #0d0d0d;
            }
        """)


class LabeledSlider(QWidget):
    """Slider avec label personnalisé"""
    
    value_changed = pyqtSignal(int)
    
    def __init__(self, label_text, min_value=-100, max_value=100, default_value=0, parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.min_value = min_value
        self.max_value = max_value
        self.default_value = default_value
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 2, 0, 5)
        layout.setSpacing(4)
        
        # Header Layout (Label + Value)
        header_layout = QHBoxLayout()
        
        # Label
        label = QLabel(self.label_text)
        label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: 500;
                font-family: 'Montserrat';
            }
        """)
        header_layout.addWidget(label)
        
        header_layout.addStretch()
        
        # Value Label
        self.value_label = QLabel(str(self.default_value))
        self.value_label.setStyleSheet("""
            QLabel {
                color: #2196F3;
                font-size: 12px;
                font-weight: bold;
                font-family: 'Montserrat';
            }
        """)
        header_layout.addWidget(self.value_label)
        
        layout.addLayout(header_layout)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(self.min_value)
        self.slider.setMaximum(self.max_value)
        self.slider.setValue(self.default_value)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #2a2a2a;
                height: 6px;
                border-radius: 8px;
                border: none;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 2px solid #2196F3;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
                border: none;
            }
            QSlider::handle:horizontal:hover {
                background: #2196F3;
                border: none;
            }
        """)
        self.slider.valueChanged.connect(self.update_label)
        self.slider.valueChanged.connect(self.value_changed.emit)
        layout.addWidget(self.slider)
        
        self.setLayout(layout)
        
    def update_label(self, value):
        """Met à jour le label de valeur"""
        self.value_label.setText(str(value))
        
    def get_value(self):
        """Retourne la valeur actuelle du slider"""
        return self.slider.value()
        
    def set_value(self, value):
        """Définit la valeur du slider"""
        self.slider.setValue(value)
        self.update_label(value)
        
    def reset(self):
        """Remet le slider à sa valeur par défaut"""
        self.slider.setValue(self.default_value)
        self.update_label(self.default_value)


class ImageCorrection(QWidget):
    """
    Composant Correction des Images
    Contient les contrôles pour correction couleurs, contraste et luminosité
    """
    
    # Signaux
    color_correction_clicked = pyqtSignal()
    contrast_changed = pyqtSignal(int)
    brightness_changed = pyqtSignal(int)
    gamma_toggled = pyqtSignal(bool)
    contrast_clahe_toggled = pyqtSignal(bool)
    denoise_toggled = pyqtSignal(bool)
    sharpen_toggled = pyqtSignal(bool)
    filters_reset_clicked = pyqtSignal()
    saturation_changed = pyqtSignal(int)
    hue_changed = pyqtSignal(int)
    temperature_changed = pyqtSignal(int)

    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ImageCorrection")  
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # En-tête
        header = QLabel("Correction des images")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                background-color: white;
                color: black;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-bottom: 2px solid #ddd;
                font-family: 'Montserrat';
            }
        """)
        main_layout.addWidget(header)
        
        # Container pour les contrôles
        controls_container = QWidget()
        controls_layout = QVBoxLayout()
        controls_layout.setContentsMargins(15, 10, 15, 10)
        controls_layout.setSpacing(10)
        controls_container.setStyleSheet("background-color: black;")
        
        # Slider Contraste
        self.contrast_slider = LabeledSlider("Contraste", -100, 100, 0)
        self.contrast_slider.value_changed.connect(self.contrast_changed.emit)
        controls_layout.addWidget(self.contrast_slider)
        
        # Slider Luminosité
        self.brightness_slider = LabeledSlider("Luminosité", -100, 100, 0)
        self.brightness_slider.value_changed.connect(self.brightness_changed.emit)
        controls_layout.addWidget(self.brightness_slider)

        # NOUVEAU : Groupe pour les filtres de couleur
        color_filters_group = QGroupBox("Filtres de couleur")
        color_filters_group.setStyleSheet("""
            QGroupBox {
                background-color: black;
                border: 2px solid white;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                color: white;
            }
        """)
        color_filters_layout = QVBoxLayout(color_filters_group)
        color_filters_layout.setSpacing(6)
        color_filters_layout.setContentsMargins(8, 15, 8, 8)

        # Sliders de couleur
        color_sliders_layout = QGridLayout()
        color_sliders_layout.setHorizontalSpacing(10)

        self.saturation_slider = LabeledSlider("Saturation", -100, 100, 0)
        self.saturation_slider.value_changed.connect(self.saturation_changed.emit)
        color_sliders_layout.addWidget(self.saturation_slider, 0, 0)

        self.hue_slider = LabeledSlider("Teinte", -90, 90, 0)
        self.hue_slider.value_changed.connect(self.hue_changed.emit)
        color_sliders_layout.addWidget(self.hue_slider, 0, 1)

        self.temperature_slider = LabeledSlider("Température", -100, 100, 0)
        self.temperature_slider.value_changed.connect(self.temperature_changed.emit)
        color_sliders_layout.addWidget(self.temperature_slider, 1, 0, 1, 2)

        color_filters_layout.addLayout(color_sliders_layout)

        controls_layout.addWidget(color_filters_group)

        
        # Groupe de boutons pour les filtres d'image avancés
        self.filters_groupbox = QGroupBox("Filtres avancés")
        self.filters_groupbox.setStyleSheet("""
            QGroupBox {
                background-color: black;
                border: 2px solid white;
                border-radius: 5px;
                margin-top: 1ex; /* Espace pour le titre */
                font-weight: bold;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left; /* Position du titre */
                padding: 0 3px;
                color: white;
            }
            QPushButton {
                background-color: #444;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:checked {
                background-color: #2196F3; /* Couleur bleue pour les filtres actifs */
                border-color: #2196F3;
            }
        """)
        filters_layout = QVBoxLayout(self.filters_groupbox)
        filters_layout.setSpacing(6)
        filters_layout.setContentsMargins(8, 8, 8, 8)
        
        self.btn_gamma = QPushButton("Correction Gamma")
        self.btn_gamma.setCheckable(True)
        self.btn_gamma.toggled.connect(self.gamma_toggled.emit)
        
        self.btn_contrast_clahe = QPushButton("Contraste (CLAHE)")
        self.btn_contrast_clahe.setCheckable(True)
        self.btn_contrast_clahe.toggled.connect(self.contrast_clahe_toggled.emit)
        
        self.btn_denoise = QPushButton("Anti-bruit")
        self.btn_denoise.setCheckable(True)
        self.btn_denoise.toggled.connect(self.denoise_toggled.emit)
        
        self.btn_sharpen = QPushButton("Netteté")
        self.btn_sharpen.setCheckable(True)
        self.btn_sharpen.toggled.connect(self.sharpen_toggled.emit)
        
        self.btn_reset_filters = QPushButton("Réinitialiser Filtres")
        self.btn_reset_filters.clicked.connect(self.filters_reset_clicked.emit)
        
        filters_layout.addWidget(self.btn_gamma)
        filters_layout.addWidget(self.btn_contrast_clahe)
        filters_layout.addWidget(self.btn_denoise)
        filters_layout.addWidget(self.btn_sharpen)
        filters_layout.addWidget(self.btn_reset_filters)
        
        controls_layout.addWidget(self.filters_groupbox)
        
        controls_layout.addStretch()
        
        controls_container.setLayout(controls_layout)
        
        # Création de la zone de défilement
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(controls_container)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: black;
            }
            QScrollBar:vertical {
                border: none;
                background: #1a1a1a;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
        self.setStyleSheet("""
                background-color: black;
                border: 2px solid white;
        """)
        
    def reset_all(self):
        """Réinitialise tous les contrôles"""
        self.contrast_slider.reset()
        self.brightness_slider.reset()
        # Réinitialiser l'état des boutons de filtre
        self.btn_gamma.setChecked(False)
        self.btn_contrast_clahe.setChecked(False)
        self.btn_denoise.setChecked(False)
        self.btn_sharpen.setChecked(False)
        # Réinitialiser les nouveaux sliders et la courbe
        self.saturation_slider.reset()
        self.hue_slider.reset()
        self.temperature_slider.reset()
        
    def get_contrast(self):
        """Retourne la valeur du contraste"""
        return self.contrast_slider.get_value()
        
    def get_brightness(self):
        """Retourne la valeur de la luminosité"""
        return self.brightness_slider.get_value()
        
    def set_contrast(self, value):
        """Définit la valeur du contraste"""
        self.contrast_slider.set_value(value)
        
    def set_brightness(self, value):
        """Définit la valeur de la luminosité"""
        self.brightness_slider.set_value(value)

    def update_filter_buttons_state(self, states: dict):
        """
        Met à jour l'état (coché/décoché) des boutons de filtre.
        """
        self.btn_gamma.setChecked(states.get('gamma', False))
        self.btn_contrast_clahe.setChecked(states.get('contrast', False))
        self.btn_denoise.setChecked(states.get('denoise', False))
        self.btn_sharpen.setChecked(states.get('sharpen', False))


# Exemple d'utilisation
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setGeometry(100, 100, 430, 400)
    window.setStyleSheet("background-color: #2a2a2a;")
    
    correction = ImageCorrection()
    
    # Connecter les signaux
    correction.color_correction_clicked.connect(lambda: print("Correction couleurs"))
    correction.contrast_changed.connect(lambda v: print(f"Contraste: {v}"))
    correction.brightness_changed.connect(lambda v: print(f"Luminosité: {v}"))
    
    window.setCentralWidget(correction)
    window.show()
    
    sys.exit(app.exec())