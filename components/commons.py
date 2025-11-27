"""
Commons
Palette, typographie et petits composants réutilisables pour l'UI.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# --------------------------------------------------------------------------- #
# Design tokens
# --------------------------------------------------------------------------- #
COLORS = {
    "bg_primary": "#0b1220",
    "bg_secondary": "#111827",
    "bg_tertiary": "#1f2937",
    "bg_glass": "rgba(17, 24, 39, 0.85)",
    "accent_cyan": "#0ea5e9",
    "accent_cyan_light": "#38bdf8",
    "text_primary": "#e5e7eb",
    "text_secondary": "#9ca3af",
    "border": "#1f2937",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#ef4444",
}

FONTS = {
    "primary": "Montserrat",
    "monospace": "JetBrains Mono",
    "sizes": {"xs": 11, "sm": 12, "base": 14, "lg": 16, "xl": 18, "2xl": 20},
}

SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24}


def _card_stylesheet(accent: bool = False, transparent: bool = False) -> str:
    bg = "transparent" if transparent else COLORS["bg_secondary"]
    border_color = COLORS["accent_cyan"] if accent else COLORS["border"]
    return (
        f"QFrame#RoundedCard {{"
        f"background-color: {bg};"
        f"border: 1px solid {border_color};"
        f"border-radius: 14px;"
        f"color: {COLORS['text_primary']};"
        f"font-family: '{FONTS['primary']}', 'Segoe UI', sans-serif;"
        f"}}"
        f"QLabel#CardTitle {{"
        f"color: {COLORS['text_primary']};"
        f"font-size: {FONTS['sizes']['lg']}px;"
        f"font-weight: 700;"
        f"}}"
        f"QLabel#CardSubtitle {{"
        f"color: {COLORS['text_secondary']};"
        f"font-size: {FONTS['sizes']['sm']}px;"
        f"font-weight: 600;"
        f"}}"
    )


class RoundedCard(QFrame):
    """Conteneur avec fond sombre arrondi."""

    def __init__(
        self,
        title: str | None = None,
        subtitle: str | None = None,
        accent: bool = False,
        padding: int = SPACING["lg"],
        transparent: bool = False,
        toolbar: Optional[QWidget] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("RoundedCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(padding, padding, padding, padding)
        layout.setSpacing(SPACING["md"])

        if title or toolbar or subtitle:
            header = QHBoxLayout()
            header.setContentsMargins(0, 0, 0, 0)
            header.setSpacing(SPACING["sm"])
            header.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            title_box = QVBoxLayout()
            title_box.setContentsMargins(0, 0, 0, 0)
            title_box.setSpacing(2)

            if title:
                title_label = QLabel(title)
                title_label.setObjectName("CardTitle")
                title_box.addWidget(title_label)
            if subtitle:
                subtitle_label = QLabel(subtitle)
                subtitle_label.setObjectName("CardSubtitle")
                title_box.addWidget(subtitle_label)

            header.addLayout(title_box, stretch=1)

            if toolbar:
                header.addWidget(toolbar, alignment=Qt.AlignmentFlag.AlignRight)

            layout.addLayout(header)

        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(SPACING["md"])
        layout.addWidget(self.body)

        self.setStyleSheet(_card_stylesheet(accent=accent, transparent=transparent))


class IconButton(QPushButton):
    """Bouton icône arrondi avec états hover/active."""

    def __init__(
        self,
        icon_text: str,
        tooltip: str = "",
        variant: str = "ghost",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.icon_text = icon_text
        self.variant = variant
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setText(icon_text)
        if tooltip:
            self.setToolTip(tooltip)
        self.setFixedSize(34, 34)
        self._apply_style()

    def _apply_style(self) -> None:
        base_bg = "transparent" if self.variant == "ghost" else COLORS["bg_tertiary"]
        base_fg = COLORS["text_primary"]
        border = COLORS["accent_cyan"] if self.variant == "outline" else "transparent"
        hover_bg = COLORS["bg_tertiary"]
        if self.variant == "primary":
            base_bg = COLORS["accent_cyan"]
            base_fg = COLORS["bg_primary"]
            hover_bg = COLORS["accent_cyan_light"]
        self.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {base_bg};"
            f"color: {base_fg};"
            f"border: 1px solid {border};"
            f"border-radius: 10px;"
            f"font-size: {FONTS['sizes']['lg']}px;"
            f"font-weight: 700;"
            f"font-family: '{FONTS['primary']}';"
            f"}}"
            f"QPushButton:hover {{ background-color: {hover_bg}; }}"
            f"QPushButton:pressed {{ background-color: {COLORS['bg_secondary']}; }}"
            f"QPushButton:disabled {{"
            f"color: {COLORS['text_secondary']};"
            f"border-color: {COLORS['border']};"
            f"}}"
        )


class Badge(QLabel):
    """Petit indicateur coloré pour les statuts."""

    def __init__(self, text: str, kind: str = "neutral", parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        palette = {
            "neutral": (COLORS["bg_tertiary"], COLORS["text_secondary"]),
            "success": (COLORS["success"], COLORS["bg_primary"]),
            "warning": (COLORS["warning"], COLORS["bg_primary"]),
            "danger": (COLORS["danger"], COLORS["bg_primary"]),
            "info": (COLORS["accent_cyan"], COLORS["bg_primary"]),
        }
        bg, fg = palette.get(kind, palette["neutral"])
        self.setStyleSheet(
            f"QLabel {{"
            f"background-color: {bg};"
            f"color: {fg};"
            f"border-radius: 8px;"
            f"padding: 2px 6px;"
            f"font-size: {FONTS['sizes']['sm']}px;"
            f"font-weight: 700;"
            f"font-family: '{FONTS['primary']}';"
            f"}}"
        )


class Toast(QWidget):
    """Notification temporaire non intrusive."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlags(Qt.WindowType.ToolTip)
        self.label = QLabel("", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(
            f"QLabel {{"
            f"background-color: rgba(12, 18, 32, 230);"
            f"color: {COLORS['text_primary']};"
            f"border: 1px solid {COLORS['accent_cyan']};"
            f"border-radius: 10px;"
            f"padding: 10px 14px;"
            f"font-weight: 600;"
            f"font-family: '{FONTS['primary']}';"
            f"}}"
        )
        self.opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)
        self.hide()
        self._anim = QPropertyAnimation(self.opacity, b"opacity", self)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)
        self._anim.finished.connect(self._handle_finished)

    def show_message(self, text: str, kind: str = "info", duration_ms: int = 2200) -> None:
        accents = {
            "info": COLORS["accent_cyan"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "danger": COLORS["danger"],
        }
        accent = accents.get(kind, COLORS["accent_cyan"])
        self.label.setText(text)
        self.label.setStyleSheet(
            f"QLabel {{"
            f"background-color: rgba(12, 18, 32, 230);"
            f"color: {COLORS['text_primary']};"
            f"border: 1px solid {accent};"
            f"border-radius: 10px;"
            f"padding: 10px 14px;"
            f"font-weight: 600;"
            f"font-family: '{FONTS['primary']}';"
            f"}}"
        )
        self.adjustSize()
        parent = self.parent() or self.window()
        if parent:
            geo = parent.geometry()
            self.move(
                geo.x() + geo.width() - self.width() - SPACING["xl"],
                geo.y() + geo.height() - self.height() - SPACING["xl"],
            )
        self._fade_in()
        self._timer.start(duration_ms)

    # ------------------------------------------------------------------ #
    # Animations
    # ------------------------------------------------------------------ #
    def _fade_in(self) -> None:
        self.show()
        self._anim.stop()
        self._anim.setDuration(160)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def _fade_out(self) -> None:
        self._anim.stop()
        self._anim.setDuration(220)
        self._anim.setStartValue(self.opacity.opacity())
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def _handle_finished(self) -> None:
        if self.opacity.opacity() <= 0.01:
            self.hide()


class StatChip(QFrame):
    """
    Indicateur compact titre/valeur, utile pour afficher une info (durée, résolution, fps).
    """

    def __init__(self, title: str, value: str, kind: str = "neutral", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatChip")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["sm"], SPACING["xs"], SPACING["sm"], SPACING["xs"])
        layout.setSpacing(0)

        title_label = QLabel(title.upper())
        title_label.setObjectName("StatChipTitle")
        value_label = QLabel(value)
        value_label.setObjectName("StatChipValue")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        palette = {
            "neutral": COLORS["bg_tertiary"],
            "info": COLORS["accent_cyan"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "danger": COLORS["danger"],
        }
        accent = palette.get(kind, COLORS["bg_tertiary"])
        self.setStyleSheet(
            f"#StatChip {{"
            f"background-color: {COLORS['bg_secondary']};"
            f"border: 1px solid {COLORS['border']};"
            f"border-radius: 10px;"
            f"}}"
            f"#StatChipTitle {{"
            f"color: {COLORS['text_secondary']};"
            f"font-size: {FONTS['sizes']['xs']}px;"
            f"letter-spacing: 0.8px;"
            f"font-weight: 700;"
            f"}}"
            f"#StatChipValue {{"
            f"color: {accent};"
            f"font-size: {FONTS['sizes']['lg']}px;"
            f"font-weight: 700;"
            f"}}"
        )


class PillButton(QPushButton):
    """Bouton pilule léger, parfait pour des filtres/presets."""

    def __init__(self, text: str, checked: bool = False, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(
            f"PillButton {{"
            f"background-color: {COLORS['bg_secondary']};"
            f"color: {COLORS['text_primary']};"
            f"border: 1px solid {COLORS['border']};"
            f"border-radius: 14px;"
            f"padding: 6px 12px;"
            f"font-weight: 700;"
            f"font-size: {FONTS['sizes']['sm']}px;"
            f"font-family: '{FONTS['primary']}';"
            f"}}"
            f"PillButton:hover {{ border-color: {COLORS['accent_cyan_light']}; }}"
            f"PillButton:checked {{"
            f"background-color: {COLORS['accent_cyan']};"
            f"color: {COLORS['bg_primary']};"
            f"border-color: {COLORS['accent_cyan_light']};"
            f"}}"
        )


class SectionTitle(QWidget):
    """En-tête compact avec titre + sous-titre optionnel."""

    def __init__(self, title: str, subtitle: str | None = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitleLabel")
        layout.addWidget(title_label)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("SectionSubtitleLabel")
            layout.addWidget(subtitle_label)

        self.setStyleSheet(
            f"#SectionTitleLabel {{"
            f"color: {COLORS['text_primary']};"
            f"font-size: {FONTS['sizes']['lg']}px;"
            f"font-weight: 800;"
            f"font-family: '{FONTS['primary']}';"
            f"}}"
            f"#SectionSubtitleLabel {{"
            f"color: {COLORS['text_secondary']};"
            f"font-size: {FONTS['sizes']['sm']}px;"
            f"font-weight: 600;"
            f"font-family: '{FONTS['primary']}';"
            f"}}"
        )
