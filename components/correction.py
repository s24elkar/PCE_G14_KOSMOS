"""
Panneau de correction des images
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSlider
from PyQt6.QtCore import Qt, pyqtSignal


class CorrectionPanel(QFrame):
    """Panneau de correction des images"""
    
    brightness_changed = pyqtSignal(int)
    contrast_changed = pyqtSignal(int)
    saturation_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Correction des images")
        title.setObjectName("panelTitle")
        layout.addWidget(title)
        
        # Luminosité
        bright_layout = QHBoxLayout()
        bright_layout.addWidget(QLabel("Luminosité:"))
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self.brightness_changed.emit)
        bright_layout.addWidget(self.brightness_slider)
        self.brightness_value = QLabel("0")
        bright_layout.addWidget(self.brightness_value)
        layout.addLayout(bright_layout)
        
        # Contraste
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(QLabel("Contraste:"))
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        self.contrast_slider.valueChanged.connect(self.contrast_changed.emit)
        contrast_layout.addWidget(self.contrast_slider)
        self.contrast_value = QLabel("0")
        contrast_layout.addWidget(self.contrast_value)
        layout.addLayout(contrast_layout)
        
        # Saturation
        saturation_layout = QHBoxLayout()
        saturation_layout.addWidget(QLabel("Saturation:"))
        self.saturation_slider = QSlider(Qt.Orientation.Horizontal)
        self.saturation_slider.setRange(-100, 100)
        self.saturation_slider.setValue(0)
        self.saturation_slider.valueChanged.connect(self.saturation_changed.emit)
        saturation_layout.addWidget(self.saturation_slider)
        self.saturation_value = QLabel("0")
        saturation_layout.addWidget(self.saturation_value)
        layout.addLayout(saturation_layout)
        
        layout.addStretch()
    
    def update_brightness_label(self, value):
        """Met à jour l'étiquette de luminosité"""
        self.brightness_value.setText(str(value))
    
    def update_contrast_label(self, value):
        """Met à jour l'étiquette de contraste"""
        self.contrast_value.setText(str(value))
    
    def update_saturation_label(self, value):
        """Met à jour l'étiquette de saturation"""
        self.saturation_value.setText(str(value))