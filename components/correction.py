"""
Composant Correction des Images
Contrôles pour correction couleurs, contraste et luminosité
"""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QPushButton,
    QToolButton,
    QGridLayout,
    QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSignalBlocker

from components.commons import COLORS, FONTS, SPACING

class ColorCorrectionButton(QPushButton):
    """Bouton de correction couleurs avec icône colorée"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        self.setText("🎨   Correction couleurs")
        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['bg_secondary']};"
            f"color: {COLORS['text_primary']};"
            f"border: 1px solid {COLORS['accent_cyan']};"
            f"border-radius: 10px;"
            f"padding: 10px 15px;"
            f"text-align: left;"
            f"font-size: {FONTS['sizes']['base']}px;"
            f"font-weight: 600;"
            f"font-family: '{FONTS['primary']}';"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: {COLORS['bg_tertiary']};"
            f"border-color: {COLORS['accent_cyan_light']};"
            f"}}"
        )


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
        label.setStyleSheet(
            f"QLabel {{"
            f"color: {COLORS['text_primary']};"
            f"font-size: {FONTS['sizes']['base']}px;"
            f"font-weight: 600;"
            f"font-family: '{FONTS['primary']}';"
            f"}}"
        )
        layout.addWidget(label)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(self.min_value)
        self.slider.setMaximum(self.max_value)
        self.slider.setValue(self.default_value)
        self.slider.setStyleSheet(
            f"QSlider::groove:horizontal {{"
            f"background: {COLORS['bg_tertiary']};"
            f"height: 6px;"
            f"border-radius: 8px;"
            f"border: none;"
            f"}}"
            f"QSlider::handle:horizontal {{"
            f"background: {COLORS['accent_cyan']};"
            f"border: 2px solid {COLORS['bg_primary']};"
            f"width: 16px;"
            f"height: 16px;"
            f"margin: -6px 0;"
            f"border-radius: 8px;"
            f"}}"
            f"QSlider::handle:horizontal:hover {{"
            f"background: {COLORS['accent_cyan_light']};"
            f"}}"
        )
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
        blocker = QSignalBlocker(self.slider)
        self.slider.setValue(self.default_value)
        del blocker


class ImageCorrection(QWidget):
    """
    Composant Correction des Images
    Contrôles avancés : couleurs, contraste, luminosité, saturation, teinte,
    température, netteté, gamma et débruitage.
    """
    
    # Signaux
    color_correction_clicked = pyqtSignal()
    contrast_changed = pyqtSignal(int)
    brightness_changed = pyqtSignal(int)
    saturation_changed = pyqtSignal(int)
    hue_changed = pyqtSignal(int)
    temperature_changed = pyqtSignal(int)
    sharpness_changed = pyqtSignal(int)
    gamma_changed = pyqtSignal(int)
    denoise_changed = pyqtSignal(int)
    apply_clicked = pyqtSignal()
    undo_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.presets = {
            "Eau claire": {"contrast": 10, "brightness": 5, "saturation": 8, "temperature": 6},
            "Eau trouble": {"contrast": 18, "brightness": 12, "saturation": 15, "denoise": 20},
            "Profondeur >50m": {"contrast": 22, "brightness": -5, "saturation": 12, "temperature": 14, "gamma": 8},
            "Nuit": {"contrast": 12, "brightness": 18, "denoise": 35, "gamma": 10},
            "Custom": {},
        }
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(SPACING["sm"])

        header = QLabel("Correction des images")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setStyleSheet(
            f"QLabel {{"
            f"background-color: {COLORS['bg_secondary']};"
            f"color: {COLORS['text_primary']};"
            f"font-size: {FONTS['sizes']['lg']}px;"
            f"font-weight: 700;"
            f"padding: 10px;"
            f"border-bottom: 1px solid {COLORS['border']};"
            f"font-family: '{FONTS['primary']}';"
            f"}}"
        )
        main_layout.addWidget(header)

        controls_container = QWidget()
        controls_layout = QVBoxLayout()
        controls_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        controls_layout.setSpacing(SPACING["md"])

        # Presets
        presets_row = QHBoxLayout()
        presets_row.setContentsMargins(0, 0, 0, 0)
        presets_row.setSpacing(SPACING["sm"])
        preset_label = QLabel("Presets :")
        preset_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-weight: 600; font-size: {FONTS['sizes']['sm']}px;"
        )
        presets_row.addWidget(preset_label)
        self.preset_buttons = []
        for name in ["Eau claire", "Eau trouble", "Profondeur >50m", "Nuit", "Custom"]:
            btn = QPushButton(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{"
                f"background-color: {COLORS['bg_secondary']};"
                f"color: {COLORS['text_primary']};"
                f"border: 1px solid {COLORS['border']};"
                f"border-radius: 10px;"
                f"padding: 6px 10px;"
                f"font-weight: 600;"
                f"}}"
                f"QPushButton:hover {{ background-color: {COLORS['bg_tertiary']}; border-color: {COLORS['accent_cyan']}; }}"
            )
            btn.clicked.connect(lambda _, preset=name: self._apply_preset(preset))
            presets_row.addWidget(btn)
            self.preset_buttons.append(btn)
        presets_row.addStretch()
        controls_layout.addLayout(presets_row)

        # Bouton Correction couleurs
        self.color_btn = ColorCorrectionButton()
        self.color_btn.clicked.connect(self.color_correction_clicked.emit)
        controls_layout.addWidget(self.color_btn)

        # Bloc niveau 1 (visibles)
        level1_grid = QGridLayout()
        level1_grid.setColumnStretch(0, 1)
        level1_grid.setColumnStretch(1, 1)
        level1_grid.setHorizontalSpacing(SPACING["md"])
        level1_grid.setVerticalSpacing(SPACING["md"])

        self.contrast_slider = LabeledSlider("Contraste", -100, 100, 0)
        self.contrast_slider.value_changed.connect(self.contrast_changed.emit)
        level1_grid.addWidget(self.contrast_slider, 0, 0)

        self.brightness_slider = LabeledSlider("Luminosité", -100, 100, 0)
        self.brightness_slider.value_changed.connect(self.brightness_changed.emit)
        level1_grid.addWidget(self.brightness_slider, 0, 1)

        controls_layout.addLayout(level1_grid)

        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(SPACING["sm"])

        self.apply_btn = QPushButton("Appliquer à l'aperçu")
        self.apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['bg_secondary']};"
            f"color: {COLORS['text_primary']};"
            f"border: 1px solid {COLORS['success']};"
            f"border-radius: 10px;"
            f"padding: 10px 12px;"
            f"font-weight: 700;"
            f"}}"
            f"QPushButton:hover {{ background-color: {COLORS['success']}; color: {COLORS['bg_primary']}; }}"
        )
        self.apply_btn.clicked.connect(self.apply_clicked.emit)
        actions_layout.addWidget(self.apply_btn)

        self.undo_btn = QPushButton("Annuler la correction")
        self.undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.undo_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['bg_secondary']};"
            f"color: {COLORS['text_primary']};"
            f"border: 1px solid {COLORS['warning']};"
            f"border-radius: 10px;"
            f"padding: 10px 12px;"
            f"font-weight: 700;"
            f"}}"
            f"QPushButton:hover {{ background-color: {COLORS['warning']}; color: {COLORS['bg_primary']}; }}"
        )
        self.undo_btn.clicked.connect(self.undo_clicked.emit)
        actions_layout.addWidget(self.undo_btn)

        self.reset_btn = QPushButton("Réinitialiser tout")
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['bg_secondary']};"
            f"color: {COLORS['text_primary']};"
            f"border: 1px solid {COLORS['danger']};"
            f"border-radius: 10px;"
            f"padding: 10px 12px;"
            f"font-weight: 700;"
            f"}}"
            f"QPushButton:hover {{ background-color: {COLORS['danger']}; color: {COLORS['bg_primary']}; }}"
        )
        self.reset_btn.clicked.connect(self.reset_all)
        actions_layout.addWidget(self.reset_btn)

        controls_layout.addLayout(actions_layout)

        # Niveau 2 : réglages avancés
        self.advanced_toggle = QToolButton()
        self.advanced_toggle.setText("Niveau 2 : Couleurs")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setChecked(False)
        self.advanced_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.advanced_toggle.setStyleSheet(
            f"QToolButton {{"
            f"background-color: {COLORS['bg_secondary']};"
            f"color: {COLORS['text_primary']};"
            f"border: 1px solid {COLORS['border']};"
            f"border-radius: 10px;"
            f"padding: 6px 10px;"
            f"font-weight: 700;"
            f"}}"
            f"QToolButton:checked {{"
            f"background-color: {COLORS['accent_cyan']};"
            f"color: {COLORS['bg_primary']};"
            f"border-color: {COLORS['accent_cyan_light']};"
            f"}}"
        )
        self.advanced_toggle.toggled.connect(self._toggle_advanced)
        controls_layout.addWidget(self.advanced_toggle, alignment=Qt.AlignmentFlag.AlignRight)

        self.advanced_container = QWidget()
        advanced_grid = QGridLayout()
        advanced_grid.setColumnStretch(0, 1)
        advanced_grid.setColumnStretch(1, 1)
        advanced_grid.setHorizontalSpacing(SPACING["md"])
        advanced_grid.setVerticalSpacing(SPACING["md"])

        self.saturation_slider = LabeledSlider("Saturation", -100, 100, 0)
        self.saturation_slider.value_changed.connect(self.saturation_changed.emit)
        advanced_grid.addWidget(self.saturation_slider, 0, 0)

        self.hue_slider = LabeledSlider("Teinte (Hue)", -90, 90, 0)
        self.hue_slider.value_changed.connect(self.hue_changed.emit)
        advanced_grid.addWidget(self.hue_slider, 0, 1)

        self.temperature_slider = LabeledSlider("Température", -50, 50, 0)
        self.temperature_slider.value_changed.connect(self.temperature_changed.emit)
        advanced_grid.addWidget(self.temperature_slider, 1, 0)

        self.gamma_slider = LabeledSlider("Gamma", -50, 50, 0)
        self.gamma_slider.value_changed.connect(self.gamma_changed.emit)
        advanced_grid.addWidget(self.gamma_slider, 1, 1)

        self.advanced_container.setLayout(advanced_grid)
        self.advanced_container.setVisible(False)
        controls_layout.addWidget(self.advanced_container)

        # Niveau 3 : expert
        self.expert_toggle = QToolButton()
        self.expert_toggle.setText("Niveau 3 : Expert")
        self.expert_toggle.setCheckable(True)
        self.expert_toggle.setChecked(False)
        self.expert_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.expert_toggle.setStyleSheet(self.advanced_toggle.styleSheet())
        self.expert_toggle.toggled.connect(self._toggle_expert)
        controls_layout.addWidget(self.expert_toggle, alignment=Qt.AlignmentFlag.AlignRight)

        self.expert_container = QWidget()
        expert_grid = QGridLayout()
        expert_grid.setColumnStretch(0, 1)
        expert_grid.setColumnStretch(1, 1)
        expert_grid.setHorizontalSpacing(SPACING["md"])
        expert_grid.setVerticalSpacing(SPACING["md"])

        self.sharpness_slider = LabeledSlider("Netteté", 0, 100, 0)
        self.sharpness_slider.value_changed.connect(self.sharpness_changed.emit)
        expert_grid.addWidget(self.sharpness_slider, 0, 0)

        self.denoise_slider = LabeledSlider("Débruitage", 0, 100, 0)
        self.denoise_slider.value_changed.connect(self.denoise_changed.emit)
        expert_grid.addWidget(self.denoise_slider, 0, 1)

        expert_info = QLabel("Courbes avancées (à venir)")
        expert_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONTS['sizes']['sm']}px;")
        expert_grid.addWidget(expert_info, 1, 0, 1, 2)

        self.expert_container.setLayout(expert_grid)
        self.expert_container.setVisible(False)
        controls_layout.addWidget(self.expert_container)

        controls_layout.addStretch()
        controls_container.setLayout(controls_layout)
        controls_container.setStyleSheet("background-color: transparent;")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        scroll_area.setWidget(controls_container)
        self.controls_scroll = scroll_area

        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)
        self.setObjectName("imageCorrection")
        self.setStyleSheet(
            f"#imageCorrection {{"
            f"background-color: transparent;"
            f"font-family: '{FONTS['primary']}', 'Segoe UI', sans-serif;"
            f"}}"
        )

    def _toggle_advanced(self, checked: bool) -> None:
        """Affiche ou masque les réglages avancés."""
        if hasattr(self, "advanced_container"):
            self.advanced_container.setVisible(checked)
        if checked and hasattr(self, "controls_scroll"):
            # S'assure que la zone avancée est dans le viewport
            self.controls_scroll.ensureWidgetVisible(self.advanced_container, xMargin=0, yMargin=12)

    def _toggle_expert(self, checked: bool) -> None:
        """Affiche ou masque les réglages experts."""
        if hasattr(self, "expert_container"):
            self.expert_container.setVisible(checked)
        if checked and hasattr(self, "controls_scroll"):
            self.controls_scroll.ensureWidgetVisible(self.expert_container, xMargin=0, yMargin=12)

    def _apply_preset(self, name: str) -> None:
        """Applique les valeurs pré-définies pour un preset."""
        values = self.presets.get(name, {})
        self.advanced_toggle.setChecked(
            any(key in values for key in ("saturation", "hue", "temperature", "gamma"))
        )
        self.expert_toggle.setChecked(any(key in values for key in ("sharpness", "denoise")))
        self.contrast_slider.set_value(int(values.get("contrast", 0)))
        self.brightness_slider.set_value(int(values.get("brightness", 0)))
        self.saturation_slider.set_value(int(values.get("saturation", 0)))
        self.hue_slider.set_value(int(values.get("hue", 0)))
        self.temperature_slider.set_value(int(values.get("temperature", 0)))
        self.gamma_slider.set_value(int(values.get("gamma", 0)))
        self.sharpness_slider.set_value(int(values.get("sharpness", 0)))
        self.denoise_slider.set_value(int(values.get("denoise", 0)))
        
    def reset_all(self):
        """Réinitialise tous les contrôles"""
        if hasattr(self, "advanced_toggle"):
            self.advanced_toggle.setChecked(False)
        if hasattr(self, "expert_toggle"):
            self.expert_toggle.setChecked(False)
        self.contrast_slider.reset()
        self.brightness_slider.reset()
        self.saturation_slider.reset()
        self.hue_slider.reset()
        self.temperature_slider.reset()
        self.sharpness_slider.reset()
        self.gamma_slider.reset()
        self.denoise_slider.reset()

    def set_corrections(self, contrast: int, brightness: int, saturation: int = 0, hue: int = 0,
                        temperature: int = 0, sharpness: int = 0, gamma: int = 0, denoise: int = 0):
        """Met à jour les sliders sans émettre les signaux utilisateur"""
        contrast_blocker = QSignalBlocker(self.contrast_slider.slider)
        brightness_blocker = QSignalBlocker(self.brightness_slider.slider)
        saturation_blocker = QSignalBlocker(self.saturation_slider.slider)
        hue_blocker = QSignalBlocker(self.hue_slider.slider)
        temperature_blocker = QSignalBlocker(self.temperature_slider.slider)
        sharpness_blocker = QSignalBlocker(self.sharpness_slider.slider)
        gamma_blocker = QSignalBlocker(self.gamma_slider.slider)
        denoise_blocker = QSignalBlocker(self.denoise_slider.slider)

        self.contrast_slider.set_value(int(contrast))
        self.brightness_slider.set_value(int(brightness))
        self.saturation_slider.set_value(int(saturation))
        self.hue_slider.set_value(int(hue))
        self.temperature_slider.set_value(int(temperature))
        self.sharpness_slider.set_value(int(sharpness))
        self.gamma_slider.set_value(int(gamma))
        self.denoise_slider.set_value(int(denoise))
        del contrast_blocker
        del brightness_blocker
        del saturation_blocker
        del hue_blocker
        del temperature_blocker
        del sharpness_blocker
        del gamma_blocker
        del denoise_blocker
        
    def get_contrast(self):
        """Retourne la valeur du contraste"""
        return self.contrast_slider.get_value()
        
    def get_brightness(self):
        """Retourne la valeur de la luminosité"""
        return self.brightness_slider.get_value()

    def get_saturation(self):
        return self.saturation_slider.get_value()

    def get_hue(self):
        return self.hue_slider.get_value()

    def get_temperature(self):
        return self.temperature_slider.get_value()

    def get_sharpness(self):
        return self.sharpness_slider.get_value()

    def get_gamma(self):
        return self.gamma_slider.get_value()

    def get_denoise(self):
        return self.denoise_slider.get_value()
        
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
    window.setGeometry(100, 100, 430, 400)
    window.setStyleSheet("background-color: #2a2a2a;")
    
    correction = ImageCorrection()
    
    # Connecter les signaux
    correction.color_correction_clicked.connect(lambda: print("🎨 Correction couleurs"))
    correction.contrast_changed.connect(lambda v: print(f"Contraste: {v}"))
    correction.brightness_changed.connect(lambda v: print(f"Luminosité: {v}"))
    
    window.setCentralWidget(correction)
    window.show()
    
    sys.exit(app.exec())
