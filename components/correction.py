"""
Composant Correction des Images
Contrôles pour correction couleurs, contraste et luminosité
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSlider, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal


class ColorCorrectionButton(QPushButton):
    """Bouton de correction couleurs avec icône colorée"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        self.setText("🎨   Correction couleurs")
        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: black;
                color: white;
                border: 2px solid white;
                border-radius: 8px;
                padding: 10px 15px;
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
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(8)
        
        # Label
        label = QLabel(self.label_text)
        label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: 500;
            }
        """)
        layout.addWidget(label)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(self.min_value)
        self.slider.setMaximum(self.max_value)
        self.slider.setValue(self.default_value)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #2a2a2a;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 2px solid #2196F3;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #2196F3;
            }
        """)
        self.slider.valueChanged.connect(self.value_changed.emit)
        layout.addWidget(self.slider)
        
        self.setLayout(layout)
        
    def get_value(self):
        """Retourne la valeur actuelle du slider"""
        return self.slider.value()
        
    def set_value(self, value):
        """Définit la valeur du slider"""
        self.slider.setValue(value)
        
    def reset(self):
        """Remet le slider à sa valeur par défaut"""
        self.slider.setValue(self.default_value)


class ImageCorrection(QWidget):
    """
    Composant Correction des Images
    Contient les contrôles pour correction couleurs, contraste et luminosité
    """
    
    # Signaux
    color_correction_clicked = pyqtSignal()
    contrast_changed = pyqtSignal(int)
    brightness_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # En-tête
        header = QLabel("Correction des images")
        header.setStyleSheet("""
            QLabel {
                background-color: white;
                color: black;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-bottom: 2px solid #ddd;
            }
        """)
        main_layout.addWidget(header)
        
        # Container pour les contrôles
        controls_container = QWidget()
        controls_layout = QVBoxLayout()
        controls_layout.setContentsMargins(15, 15, 15, 15)
        controls_layout.setSpacing(20)
        
        # Bouton Correction couleurs
        self.color_btn = ColorCorrectionButton()
        self.color_btn.clicked.connect(self.color_correction_clicked.emit)
        controls_layout.addWidget(self.color_btn)
        
        # Slider Contraste
        self.contrast_slider = LabeledSlider("Contraste", -100, 100, 0)
        self.contrast_slider.value_changed.connect(self.contrast_changed.emit)
        controls_layout.addWidget(self.contrast_slider)
        
        # Slider Luminosité
        self.brightness_slider = LabeledSlider("Luminosité", -100, 100, 0)
        self.brightness_slider.value_changed.connect(self.brightness_changed.emit)
        controls_layout.addWidget(self.brightness_slider)
        
        controls_layout.addStretch()
        
        controls_container.setLayout(controls_layout)
        controls_container.setStyleSheet("background-color: black;")
        
        main_layout.addWidget(controls_container)
        
        self.setLayout(main_layout)
        self.setStyleSheet("""
            QWidget {
                background-color: black;
                border: 2px solid white;
            }
        """)
        
    def reset_all(self):
        """Réinitialise tous les contrôles"""
        self.contrast_slider.reset()
        self.brightness_slider.reset()
        
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


# Exemple d'utilisation
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setGeometry(100, 100, 450, 400)
    window.setStyleSheet("background-color: #2a2a2a;")
    
    correction = ImageCorrection()
    
    # Connecter les signaux
    correction.color_correction_clicked.connect(lambda: print("🎨 Correction couleurs"))
    correction.contrast_changed.connect(lambda v: print(f"Contraste: {v}"))
    correction.brightness_changed.connect(lambda v: print(f"Luminosité: {v}"))
    
    window.setCentralWidget(correction)
    window.show()
    
    sys.exit(app.exec())