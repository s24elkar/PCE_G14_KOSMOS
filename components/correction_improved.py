"""
Module de correction modernisé : presets + carte unifiée.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from components.commons import COLORS, FONTS, SPACING, PillButton, RoundedCard, SectionTitle
from components.correction import ImageCorrection


class AdvancedCorrection(QWidget):
    """
    Enveloppe ImageCorrection avec :
    - presets cliquables
    - carte visuelle unique
    Les signaux sont réémis pour rester compatibles avec le contrôleur.
    """

    color_correction_clicked = pyqtSignal()
    contrast_changed = pyqtSignal(int)
    brightness_changed = pyqtSignal(int)
    saturation_changed = pyqtSignal(int)
    hue_changed = pyqtSignal(int)
    temperature_changed = pyqtSignal(int)
    sharpness_changed = pyqtSignal(int)
    gamma_changed = pyqtSignal(int)
    denoise_changed = pyqtSignal(int)
    curve_changed = pyqtSignal(list)
    apply_clicked = pyqtSignal()
    undo_clicked = pyqtSignal()
    preset_selected = pyqtSignal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.presets = {
            "Claire": {"contrast": 10, "brightness": 4, "saturation": 10, "temperature": 6},
            "Trouble": {"contrast": 18, "brightness": 12, "saturation": 15, "denoise": 20},
            "Profonde": {"contrast": 22, "brightness": -5, "saturation": 12, "temperature": 14, "gamma": 8},
            "Nuit": {"contrast": 12, "brightness": 18, "denoise": 35, "gamma": 10},
            "Reset": {},
        }
        self._init_ui()
        self._wire_signals()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        card = RoundedCard(
            "Corrections & presets",
            subtitle="Ajustez rapidement selon les conditions de plongée",
            padding=SPACING["lg"],
        )

        # Presets
        preset_row = QHBoxLayout()
        preset_row.setContentsMargins(0, 0, 0, 0)
        preset_row.setSpacing(SPACING["sm"])
        preset_row.addWidget(SectionTitle("Presets", "Raccourcis terrain"))
        preset_row.addStretch()
        self.preset_buttons: dict[str, PillButton] = {}
        for name in self.presets:
            btn = PillButton(name)
            btn.clicked.connect(lambda checked, n=name: self.apply_preset(n))
            preset_row.addWidget(btn)
            self.preset_buttons[name] = btn
        card.body_layout.addLayout(preset_row)

        # Bloc contrôle existant
        self.base = ImageCorrection()
        card.body_layout.addWidget(self.base)
        layout.addWidget(card)

        self.setLayout(layout)
        self.setObjectName("AdvancedCorrection")
        self.setStyleSheet(
            f"#AdvancedCorrection {{ background-color: transparent; }}"
            f"QLabel {{ font-family: '{FONTS['primary']}'; }}"
        )

    def _wire_signals(self) -> None:
        # Propager les signaux du widget d'origine
        self.base.color_correction_clicked.connect(self.color_correction_clicked.emit)
        self.base.contrast_changed.connect(self.contrast_changed.emit)
        self.base.brightness_changed.connect(self.brightness_changed.emit)
        self.base.saturation_changed.connect(self.saturation_changed.emit)
        self.base.hue_changed.connect(self.hue_changed.emit)
        self.base.temperature_changed.connect(self.temperature_changed.emit)
        self.base.sharpness_changed.connect(self.sharpness_changed.emit)
        self.base.gamma_changed.connect(self.gamma_changed.emit)
        self.base.denoise_changed.connect(self.denoise_changed.emit)
        self.base.apply_clicked.connect(self.apply_clicked.emit)
        self.base.undo_clicked.connect(self.undo_clicked.emit)
        if hasattr(self.base, "curve_changed"):
            self.base.curve_changed.connect(self.curve_changed.emit)

    # ------------------------------------------------------------------ #
    # API publique
    # ------------------------------------------------------------------ #
    def apply_preset(self, name: str) -> None:
        values = self.presets.get(name, {})
        if not values:
            # Reset complet
            self.base.reset_all()
            values = {
                "contrast": 0,
                "brightness": 0,
                "saturation": 0,
                "hue": 0,
                "temperature": 0,
                "sharpness": 0,
                "gamma": 0,
                "denoise": 0,
            }
        else:
            self.base.set_corrections(**values)
        self.preset_selected.emit(values)
        self.apply_clicked.emit()

    def set_corrections(self, **kwargs) -> None:
        self.base.set_corrections(**kwargs)

    def reset_all(self) -> None:
        self.base.reset_all()

    # Les getters restent les mêmes que le widget de base
    def get_contrast(self):
        return self.base.get_contrast()

    def get_brightness(self):
        return self.base.get_brightness()

    def get_saturation(self):
        return self.base.get_saturation()

    def get_hue(self):
        return self.base.get_hue()

    def get_temperature(self):
        return self.base.get_temperature()

    def get_sharpness(self):
        return self.base.get_sharpness()

    def get_gamma(self):
        return self.base.get_gamma()

    def get_denoise(self):
        return self.base.get_denoise()
