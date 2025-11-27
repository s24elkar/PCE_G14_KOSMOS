"""
Composant Lecteur Vidéo
Lecteur avec timeline, contrôles et affichage des métadonnées
"""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QFrame,
    QDialog,
    QGraphicsOpacityEffect,
)
from PyQt6.QtCore import QEvent, QEasingCurve, QPropertyAnimation, Qt, pyqtSignal, QTimer, QRect
from PyQt6.QtGui import QColor, QPainter, QPen, QImage, QPixmap
import cv2
import numpy as np

from components.commons import COLORS, FONTS, SPACING, IconButton


class MetadataOverlay(QWidget):
    """Overlay minimaliste pour afficher les métadonnées de la vidéo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._visible_flag = True
        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._anim = QPropertyAnimation(self._opacity, b"opacity", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.finished.connect(self._on_animation_finished)
        self._build_ui()

    def _build_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.setSpacing(SPACING["xs"])

        label_style = (
            f"QLabel {{"
            f"color: {COLORS['text_primary']};"
            f"font-size: {FONTS['sizes']['sm']}px;"
            f"font-family: '{FONTS['monospace']}';"
            f"font-weight: 600;"
            f"}}"
        )

        self.time_label = QLabel("00:00 / --:--")
        self.temp_label = QLabel("Temp: -")
        self.salinity_label = QLabel("Salinité: -")
        self.depth_label = QLabel("Profondeur: -")
        self.pression_label = QLabel("Pression: -")

        for label in (
            self.time_label,
            self.temp_label,
            self.salinity_label,
            self.depth_label,
            self.pression_label,
        ):
            label.setStyleSheet(label_style)
            layout.addWidget(label)

        layout.addStretch()
        self.setStyleSheet(
            f"MetadataOverlay {{"
            f"background-color: rgba(0, 0, 0, 0.6);"
            f"border-left: 4px solid {COLORS['accent_cyan']};"
            f"border-radius: 10px;"
            f"}}"
        )

    def update_metadata(self, time=None, temp=None, salinity=None, depth=None, pression=None):
        """Met à jour les métadonnées affichées."""
        if time is not None:
            self.time_label.setText(f"{time}")
        if temp is not None:
            self.temp_label.setText(f"Temp: {temp}")
        if salinity is not None:
            self.salinity_label.setText(f"Salinité: {salinity}")
        if depth is not None:
            self.depth_label.setText(f"Profondeur: {depth}")
        if pression is not None:
            self.pression_label.setText(f"Pression: {pression}")

    def set_visible(self, visible: bool, animated: bool = True) -> None:
        """Affiche/masque l'overlay avec une légère animation."""
        self._visible_flag = visible
        if not animated:
            self.setVisible(visible)
            self._opacity.setOpacity(1.0 if visible else 0.0)
            return

        self._anim.stop()
        self._anim.setStartValue(self._opacity.opacity())
        self._anim.setEndValue(1.0 if visible else 0.0)
        if visible:
            self.show()
        self._anim.start()

    def is_overlay_visible(self) -> bool:
        return self._visible_flag

    def _on_animation_finished(self) -> None:
        if not self._visible_flag:
            self.hide()


class VideoTimeline(QWidget):
    """Timeline améliorée avec marqueurs typés et prévisualisation."""

    position_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.markers: list[dict] = []
        self.export_range: tuple[int, int] | None = None
        self.current_value = 0
        self.duration_seconds = 0.0
        self._hover_value: int | None = None
        self._hover_pos: float | None = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self._on_value_changed)
        self.slider.setFixedHeight(30)
        self.slider.setMouseTracking(True)
        self.slider.installEventFilter(self)

        self.slider.setStyleSheet(
            f"QSlider::groove:horizontal {{"
            f"background: transparent;"
            f"height: 0px;"
            f"margin: 0px;"
            f"}}"
            f"QSlider::handle:horizontal {{"
            f"background: {COLORS['accent_cyan']};"
            f"border: 2px solid {COLORS['bg_primary']};"
            f"width: 16px;"
            f"height: 16px;"
            f"margin: -9px 0;"
            f"border-radius: 9px;"
            f"}}"
            f"QSlider::handle:horizontal:hover {{"
            f"background: {COLORS['accent_cyan_light']};"
            f"}}"
        )

        layout.addWidget(self.slider)
        self.setLayout(layout)
        self.setMouseTracking(True)

    # ------------------------------------------------------------------ #
    # API publique
    # ------------------------------------------------------------------ #
    def add_marker(self, position: int, kind: str = "poi", label: str | None = None) -> None:
        """Ajoute un marqueur (position 0-1000)."""
        if 0 <= position <= 1000:
            self.markers.append({"position": position, "kind": kind, "label": label})
            self.update()

    def set_markers(self, markers: list[dict]) -> None:
        self.markers = markers or []
        self.update()

    def clear_markers(self) -> None:
        self.markers.clear()
        self.update()

    def get_position(self) -> int:
        return self.slider.value()

    def set_position(self, position: int):
        self.slider.setValue(max(0, min(1000, position)))

    def set_duration_seconds(self, seconds: float) -> None:
        self.duration_seconds = max(0.0, seconds)

    def set_export_range(self, start: int | None, end: int | None) -> None:
        """Définit la zone sélectionnée pour l'export (0-1000)."""
        if start is None or end is None:
            self.export_range = None
        else:
            start = max(0, min(1000, start))
            end = max(0, min(1000, end))
            if start > end:
                start, end = end, start
            self.export_range = (start, end)
        self.update()

    # ------------------------------------------------------------------ #
    # Events
    # ------------------------------------------------------------------ #
    def _on_value_changed(self, value):
        self.current_value = value
        self.update()
        self.position_changed.emit(value)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        track = self.slider.geometry()
        groove_left = track.x() + 12
        groove_right = track.x() + track.width() - 12
        groove_width = max(1, groove_right - groove_left)
        groove_y = track.y() + track.height() // 2
        groove_rect = QRect(groove_left, groove_y - 5, groove_width, 10)

        # Fond du track
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORS["bg_tertiary"]))
        painter.drawRoundedRect(groove_rect, 6, 6)

        # Zone d'export
        if self.export_range:
            start_x = groove_left + (self.export_range[0] / 1000.0) * groove_width
            end_x = groove_left + (self.export_range[1] / 1000.0) * groove_width
            selection_rect = QRect(int(start_x), groove_rect.top() - 3, int(end_x - start_x), groove_rect.height() + 6)
            selection_color = QColor(COLORS["accent_cyan"])
            selection_color.setAlpha(60)
            painter.setBrush(selection_color)
            painter.setPen(QPen(QColor(COLORS["accent_cyan"]), 1, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(selection_rect, 6, 6)

        # Marqueurs typés
        marker_styles = {
            "poi": ("🔴", COLORS["danger"]),
            "annotation": ("📌", COLORS["accent_cyan"]),
            "anomaly": ("⚠️", COLORS["warning"]),
        }
        for marker in self.markers:
            pos = marker.get("position", 0)
            kind = marker.get("kind", "poi")
            icon, color = marker_styles.get(kind, marker_styles["poi"])
            x = groove_left + (pos / 1000.0) * groove_width
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(QRect(int(x) - 1, groove_rect.top() - 6, 2, groove_rect.height() + 12))
            painter.setPen(QPen(QColor(color)))
            painter.drawText(int(x) - 8, groove_rect.top() - 10, icon)

        # Tooltip hover
        if self._hover_pos is not None and self._hover_value is not None:
            tooltip = self._format_time(self._hover_value)
            metrics = painter.fontMetrics()
            text_width = metrics.horizontalAdvance(tooltip)
            bubble_width = text_width + 12
            bubble_rect = QRect(
                int(self._hover_pos - bubble_width / 2),
                groove_rect.top() - 30,
                bubble_width,
                22,
            )
            painter.setPen(QPen(QColor(COLORS["accent_cyan"])))
            painter.setBrush(QColor(COLORS["bg_secondary"]))
            painter.drawRoundedRect(bubble_rect, 8, 8)
            painter.setPen(QColor(COLORS["text_primary"]))
            painter.drawText(bubble_rect, Qt.AlignmentFlag.AlignCenter, tooltip)

    def eventFilter(self, obj, event):
        if obj is self.slider:
            if event.type() in (QEvent.Type.MouseMove, QEvent.Type.Enter):
                self._update_hover(event.position().x())
            elif event.type() == QEvent.Type.Leave:
                self._hover_pos = None
                self._hover_value = None
                self.update()
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _update_hover(self, x: float) -> None:
        track = self.slider.geometry()
        left = track.x() + 12
        right = track.x() + track.width() - 12
        x = max(left, min(right, x))
        self._hover_pos = x
        ratio = (x - left) / max(1.0, (right - left))
        self._hover_value = int(ratio * 1000)
        self.update()

    def _format_time(self, value: int) -> str:
        if self.duration_seconds > 0:
            seconds = (value / 1000.0) * self.duration_seconds
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins:02d}:{secs:02d}"
        return f"{int(value/10)}%"


class VideoControls(QWidget):
    """Contrôles de lecture vidéo"""
    
    play_pause_clicked = pyqtSignal()
    previous_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    rewind_clicked = pyqtSignal()
    forward_clicked = pyqtSignal()
    speed_up_clicked = pyqtSignal()
    speed_down_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_playing = False
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(SPACING["lg"], SPACING["sm"], SPACING["lg"], SPACING["sm"])
        layout.setSpacing(SPACING["md"])

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(SPACING["sm"])

        self.prev_btn = self._make_button("⏮", "Vidéo précédente (Ctrl+↑)")
        self.prev_btn.clicked.connect(self.previous_clicked.emit)
        nav_layout.addWidget(self.prev_btn)

        self.rewind_btn = self._make_button("⏪", "Reculer 5s (←)")
        self.rewind_btn.clicked.connect(self.rewind_clicked.emit)
        nav_layout.addWidget(self.rewind_btn)

        self.play_pause_btn = self._make_button("▶", "Lecture/Pause (Espace)", accent=True)
        self.play_pause_btn.setFixedWidth(56)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        nav_layout.addWidget(self.play_pause_btn)

        self.forward_btn = self._make_button("⏩", "Avancer 5s (→)")
        self.forward_btn.clicked.connect(self.forward_clicked.emit)
        nav_layout.addWidget(self.forward_btn)

        self.next_btn = self._make_button("⏭", "Vidéo suivante (Ctrl+↓)")
        self.next_btn.clicked.connect(self.next_clicked.emit)
        nav_layout.addWidget(self.next_btn)

        layout.addLayout(nav_layout)

        # Vitesse
        speed_layout = QHBoxLayout()
        speed_layout.setSpacing(SPACING["xs"])
        self.speed_down_btn = self._make_button("−", "Vitesse -", compact=True)
        self.speed_down_btn.clicked.connect(self.speed_down_clicked.emit)
        speed_layout.addWidget(self.speed_down_btn)

        self.speed_label = QLabel("x1.0")
        self.speed_label.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-weight: 700; font-size: {FONTS['sizes']['base']}px;"
        )
        speed_layout.addWidget(self.speed_label)

        self.speed_up_btn = self._make_button("+", "Vitesse +", compact=True)
        self.speed_up_btn.clicked.connect(self.speed_up_clicked.emit)
        speed_layout.addWidget(self.speed_up_btn)
        layout.addLayout(speed_layout)

        layout.addStretch()

        self.state_label = QLabel("En pause")
        self.state_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-weight: 600; font-size: {FONTS['sizes']['sm']}px;"
        )
        layout.addWidget(self.state_label)

        self.setLayout(layout)
        self.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border-radius: 10px;")
        
    def toggle_play_pause(self):
        """Bascule entre lecture et pause"""
        self.is_playing = not self.is_playing
        self.play_pause_btn.setText("⏸" if self.is_playing else "▶")
        self.state_label.setText("Lecture" if self.is_playing else "En pause")
        self.play_pause_clicked.emit()

    def set_speed_label(self, speed: float):
        """Met à jour le label de vitesse affiché."""
        self.speed_label.setText(f"x{speed:.1f}")

    def _make_button(self, text: str, tooltip: str = "", accent: bool = False, compact: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(40 if not compact else 32)
        if not compact:
            btn.setFixedWidth(48)
        if tooltip:
            btn.setToolTip(tooltip)

        base_bg = COLORS["bg_tertiary"]
        fg = COLORS["text_primary"]
        hover_bg = COLORS["bg_secondary"]
        if accent:
            base_bg = COLORS["accent_cyan"]
            fg = COLORS["bg_primary"]
            hover_bg = COLORS["accent_cyan_light"]

        btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {base_bg};"
            f"color: {fg};"
            f"border: 1px solid {COLORS['border']};"
            f"border-radius: 10px;"
            f"padding: 8px 12px;"
            f"font-weight: 700;"
            f"font-size: {FONTS['sizes']['base']}px;"
            f"font-family: '{FONTS['primary']}';"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: {hover_bg};"
            f"border-color: {COLORS['accent_cyan']};"
            f"}}"
            f"QPushButton:pressed {{"
            f"background-color: {COLORS['bg_primary']};"
            f"}}"
            f"QPushButton:disabled {{"
            f"color: {COLORS['text_secondary']};"
            f"border-color: {COLORS['border']};"
            f"}}"
        )
        return btn


class VideoPlayer(QWidget):
    """
    Composant Lecteur Vidéo
    Lecteur avec overlay de métadonnées, timeline et contrôles
    """
    
    # Signaux
    play_pause_clicked = pyqtSignal()
    position_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.playback_speed = 1.0
        self.metadata_visible = True
        self.external_window = None
        self.external_label = None
        self._last_pixmap: QPixmap | None = None
        self._metadata_timer = QTimer(self)
        self._metadata_timer.setSingleShot(True)
        self._metadata_timer.timeout.connect(self._auto_hide_overlay)
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(SPACING["sm"])

        # Zone vidéo
        video_container = QFrame()
        video_container.setObjectName("VideoContainer")
        video_container.setMinimumHeight(420)
        video_container.setStyleSheet(
            f"#VideoContainer {{"
            f"background-color: {COLORS['bg_secondary']};"
            f"border: 1px solid {COLORS['border']};"
            f"border-radius: 14px;"
            f"}}"
        )
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        video_layout.setSpacing(SPACING["sm"])

        self.video_frame = QLabel()
        self.video_frame.setObjectName("VideoSurface")
        self.video_frame.setStyleSheet(
            f"#VideoSurface {{"
            f"background-color: {COLORS['bg_primary']};"
            f"border: 1px solid {COLORS['border']};"
            f"border-radius: 12px;"
            f"}}"
        )
        self.video_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_frame.setMinimumHeight(420)
        self.video_frame.setMouseTracking(True)
        self.video_frame.installEventFilter(self)
        video_layout.addWidget(self.video_frame)

        # Overlay métadonnées + contrôles flottants
        self.metadata_overlay = MetadataOverlay(self.video_frame)
        self.metadata_overlay.move(SPACING["lg"], SPACING["lg"])
        self.metadata_overlay.show()

        self.metadata_toggle_btn = IconButton("🛈", tooltip="Afficher/masquer les métadonnées (M)", parent=self.video_frame)
        self.metadata_toggle_btn.clicked.connect(self.toggle_metadata_overlay)

        self.fullscreen_btn = IconButton("⛶", tooltip="Ouvrir dans une fenêtre dédiée", parent=self.video_frame)
        self.fullscreen_btn.clicked.connect(self.open_external_window)

        video_container.setLayout(video_layout)
        main_layout.addWidget(video_container)

        # Timeline améliorée
        timeline_container = QFrame()
        timeline_container.setObjectName("TimelineContainer")
        timeline_container.setStyleSheet(
            f"#TimelineContainer {{"
            f"background-color: {COLORS['bg_secondary']};"
            f"border: 1px solid {COLORS['border']};"
            f"border-radius: 12px;"
            f"}}"
        )
        timeline_layout = QVBoxLayout()
        timeline_layout.setContentsMargins(SPACING["lg"], SPACING["sm"], SPACING["lg"], SPACING["sm"])
        timeline_layout.setSpacing(SPACING["xs"])

        self.timeline = VideoTimeline()
        self.timeline.position_changed.connect(self.position_changed.emit)
        timeline_layout.addWidget(self.timeline)

        self.timecode_label = QLabel("00:00 / --:--")
        self.timecode_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONTS['sizes']['sm']}px; font-weight: 600;"
        )
        timeline_layout.addWidget(self.timecode_label, alignment=Qt.AlignmentFlag.AlignRight)

        timeline_container.setLayout(timeline_layout)
        main_layout.addWidget(timeline_container)

        # Contrôles
        self.controls = VideoControls()
        self.controls.play_pause_clicked.connect(self.play_pause_clicked.emit)
        self.controls.speed_up_clicked.connect(self.increase_speed)
        self.controls.speed_down_clicked.connect(self.decrease_speed)
        self.controls.set_speed_label(self.playback_speed)
        main_layout.addWidget(self.controls)

        self.setLayout(main_layout)
        self.setObjectName("VideoPlayer")
        self.setStyleSheet(
            f"#VideoPlayer {{"
            f"background-color: {COLORS['bg_primary']};"
            f"}}"
            f"QLabel {{"
            f"color: {COLORS['text_primary']};"
            f"font-family: '{FONTS['primary']}';"
            f"}}"
        )
        self._restart_metadata_timer()
        
    def resizeEvent(self, event):
        """Redimensionne l'overlay et le bouton plein écran quand le widget change de taille"""
        super().resizeEvent(event)
        if hasattr(self, "metadata_overlay"):
            overlay_width = min(int(self.video_frame.width() * 0.4), 320)
            self.metadata_overlay.setFixedWidth(max(180, overlay_width))
            self.metadata_overlay.adjustSize()
            self.metadata_overlay.move(SPACING["lg"], SPACING["lg"])
        margin = SPACING["lg"]
        if hasattr(self, "fullscreen_btn"):
            btn_x = self.video_frame.width() - self.fullscreen_btn.width() - margin
            btn_y = self.video_frame.height() - self.fullscreen_btn.height() - margin
            self.fullscreen_btn.move(btn_x, btn_y)
        if hasattr(self, "metadata_toggle_btn"):
            meta_x = self.video_frame.width() - self.metadata_toggle_btn.width() - margin
            meta_y = margin
            self.metadata_toggle_btn.move(meta_x, meta_y)
            
    def update_metadata(self, **kwargs):
        """Met à jour les métadonnées affichées"""
        self.metadata_overlay.update_metadata(**kwargs)
        timecode = kwargs.get("timecode") or kwargs.get("time")
        duration = kwargs.get("duration")
        if timecode and duration:
            self.timecode_label.setText(f"{timecode} / {duration}")
        elif timecode:
            self.timecode_label.setText(str(timecode))
        if "duration_seconds" in kwargs:
            self.timeline.set_duration_seconds(kwargs.get("duration_seconds", 0.0))
        self._on_user_activity()
        
    def set_position(self, position):
        """Définit la position de lecture (0-1000)"""
        self.timeline.set_position(position)
        
    def get_position(self):
        """Retourne la position actuelle (0-1000)"""
        return self.timeline.get_position()
        
    def add_timeline_marker(self, position, kind: str = "poi", label: str | None = None):
        """Ajoute un marqueur typé (0-1000 ou pourcentage 0-100)."""
        if 0 <= position <= 100:
            position = int(position * 10)
        self.timeline.add_marker(position, kind=kind, label=label)

    def clear_timeline_markers(self):
        """Supprime tous les marqueurs de la timeline"""
        self.timeline.clear_markers()

    def set_markers(self, markers: list[dict]) -> None:
        """Remplace les marqueurs actuels par une liste."""
        self.timeline.clear_markers()
        if not markers:
            return
        for marker in markers:
            self.timeline.add_marker(
                marker.get("position", 0),
                kind=marker.get("kind", "poi"),
                label=marker.get("label"),
            )

    def set_duration_seconds(self, seconds: float) -> None:
        """Expose la durée totale pour les info-bulles de timeline."""
        self.timeline.set_duration_seconds(seconds)

    def set_export_range(self, start: int | None, end: int | None) -> None:
        """Affiche ou nettoie la zone d'export sur la timeline."""
        if start is None or end is None:
            self.timeline.set_export_range(0, 0) if hasattr(self.timeline, "set_export_range") else None
            return
        self.timeline.set_export_range(start, end)

    def eventFilter(self, obj, event):
        if obj is self.video_frame:
            if event.type() in (QEvent.Type.MouseMove, QEvent.Type.Enter):
                self._on_user_activity()
            elif event.type() == QEvent.Type.Leave:
                self._start_hide_timer()
        return super().eventFilter(obj, event)

    def charger_video(self, path: str) -> None:
        """Compatibilité avec l'ancien appel: réinitialise l'affichage."""
        self.video_frame.clear()
        self._last_pixmap = None
        self._render_external_frame()

    def set_frame(self, frame_rgb):
        """
        Affiche un frame RGB numpy dans le placeholder vidéo.
        """
        if frame_rgb is None:
            return
        h, w, _ = frame_rgb.shape
        qimg = QImage(frame_rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        scaled = pix.scaled(
            self.video_frame.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_frame.setPixmap(scaled)
        self._last_pixmap = scaled
        self._render_external_frame()

    def apply_corrections(
        self,
        contrast: int = 0,
        brightness: int = 0,
        saturation: int = 0,
        hue: int = 0,
        temperature: int = 0,
        sharpness: int = 0,
        gamma: int = 0,
        denoise: int = 0,
    ):
        """
        Applique visuellement les corrections sur le frame courant (fallback gradient si pas de frame).
        """
        if self._last_pixmap is None:
            # Fallback: gradient simulé si aucun frame n'est chargé
            factor = max(0.2, 1 + (contrast / 200.0))
            shift = brightness * 1.5
            def adjust(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
                r, g, b = rgb
                r = max(0, min(255, int(r * factor + shift)))
                g = max(0, min(255, int(g * factor + shift)))
                b = max(0, min(255, int(b * factor + shift)))
                return (r, g, b)
            colors = [
                adjust((74, 85, 104)),
                adjust((102, 124, 153)),
                adjust((139, 163, 199)),
            ]
            gradient = (
                f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
                f" stop:0 rgb{colors[0]}, stop:0.5 rgb{colors[1]}, stop:1 rgb{colors[2]});"
            )
            self.video_frame.setStyleSheet(
                f"QLabel {{{gradient} border: 1px solid {COLORS['border']}; border-radius: 12px;}}"
            )
            self._render_external_frame()
            return

        frame = self._pixmap_to_rgb(self._last_pixmap)

        # 1) Contraste / Luminosité
        alpha = max(0.2, 1 + contrast / 100.0)
        beta = brightness * 1.0
        frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

        # 2) Saturation + Hue
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV).astype(np.float32)
        # Hue est sur 0-179 ; hue slider [-90,90] -> [-45,45] (deg/2)
        hsv[:, :, 0] = (hsv[:, :, 0] + hue / 2.0) % 180
        sat_factor = max(0.0, 1 + (saturation / 100.0))
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat_factor, 0, 255)
        frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

        # 3) Température (ajuste les canaux R/B)
        if temperature != 0:
            t = np.clip(temperature, -100, 100)
            warm = np.clip(frame[:, :, 0].astype(np.int32) - t, 0, 255)  # B
            cool = np.clip(frame[:, :, 2].astype(np.int32) + t, 0, 255)  # R
            frame[:, :, 0] = warm
            frame[:, :, 2] = cool

        # 4) Gamma
        if gamma != 0:
            gamma_factor = np.interp(gamma, [-50, 0, 50], [0.5, 1.0, 2.0])
            inv = 1.0 / max(0.01, gamma_factor)
            table = (np.arange(256) / 255.0) ** inv * 255.0
            table = np.clip(table, 0, 255).astype(np.uint8)
            frame = cv2.LUT(frame, table)

        # 5) Netteté (unsharp mask)
        if sharpness > 0:
            amt = sharpness / 50.0  # 0..2
            blurred = cv2.GaussianBlur(frame, (0, 0), sigmaX=1.2)
            mask = cv2.addWeighted(frame, 1 + amt, blurred, -amt, 0)
            frame = np.clip(mask, 0, 255).astype(np.uint8)

        # 6) Débruitage
        if denoise > 0:
            h_val = np.interp(denoise, [0, 100], [0, 15])
            frame = cv2.fastNlMeansDenoisingColored(frame, None, h_val, h_val, 7, 21)

        # Sauvegarder et afficher
        h, w, _ = frame.shape
        qimg = QImage(frame.data, w, h, 3 * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        scaled = pix.scaled(
            self.video_frame.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_frame.setPixmap(scaled)
        self._last_pixmap = scaled
        self._render_external_frame()

    def _pixmap_to_rgb(self, pixmap: QPixmap) -> np.ndarray:
        """Convertit un QPixmap en numpy RGB."""
        image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGB888)
        w = image.width()
        h = image.height()
        ptr = image.bits()
        ptr.setsize(image.byteCount())
        arr = np.frombuffer(ptr, np.uint8).reshape((h, w, 3))
        return arr.copy()

    def toggle_metadata_overlay(self):
        """Affiche/masque les métadonnées."""
        self.metadata_visible = not self.metadata_visible
        if self.metadata_visible:
            self.metadata_overlay.set_visible(True, animated=True)
            self.metadata_toggle_btn.setText("🛈")
            self._restart_metadata_timer()
        else:
            self._metadata_timer.stop()
            self.metadata_overlay.set_visible(False, animated=True)
            self.metadata_toggle_btn.setText("🙈")
        self._render_external_frame()

    def increase_speed(self):
        """Augmente la vitesse de lecture simulée."""
        self.playback_speed = min(self.playback_speed * 2, 8.0)
        self.controls.set_speed_label(self.playback_speed)

    def decrease_speed(self):
        """Réduit la vitesse de lecture simulée."""
        self.playback_speed = max(self.playback_speed / 2, 0.25)
        self.controls.set_speed_label(self.playback_speed)

    def open_external_window(self):
        """Ouvre une fenêtre séparée qui suit la vidéo courante."""
        if self.external_window is None:
            self.external_window = QDialog(self)
            self.external_window.setWindowTitle("Lecture séparée")
            self.external_window.setMinimumSize(400, 300)
            layout = QVBoxLayout(self.external_window)
            self.external_label = QLabel()
            self.external_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.external_label.setStyleSheet("background-color: black; color: white;")
            layout.addWidget(self.external_label)
        self._render_external_frame()
        self.external_window.show()
        self.external_window.raise_()

    def _render_external_frame(self):
        """Mets à jour la fenêtre séparée si elle est ouverte."""
        if self.external_window and self.external_window.isVisible() and self.external_label:
            if self._last_pixmap:
                scaled = self._last_pixmap.scaled(
                    self.external_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.external_label.setPixmap(scaled)
                self.external_label.setText("")
            else:
                self.external_label.setText("Aucune vidéo")

    def _on_user_activity(self) -> None:
        if not self.metadata_visible:
            return
        self.metadata_overlay.set_visible(True, animated=True)
        self._restart_metadata_timer()

    def _restart_metadata_timer(self) -> None:
        if self.metadata_visible:
            self._metadata_timer.start(3000)

    def _start_hide_timer(self) -> None:
        if self.metadata_visible:
            self._metadata_timer.start(3000)

    def _auto_hide_overlay(self) -> None:
        if self.metadata_visible:
            self.metadata_overlay.set_visible(False, animated=True)

    def metadata_is_visible(self) -> bool:
        """Expose l'état d'affichage des métadonnées."""
        return self.metadata_visible


# Exemple d'utilisation
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setGeometry(100, 100, 700, 500)
    window.setStyleSheet("background-color: #1a1a1a;")
    
    player = VideoPlayer()
    
    # Connecter les signaux
    player.play_pause_clicked.connect(lambda: print("▶/⏸ Play/Pause"))
    player.position_changed.connect(lambda pos: print(f"Position: {pos}"))
    player.controls.previous_clicked.connect(lambda: print("⏮ Précédent"))
    player.controls.next_clicked.connect(lambda: print("⏭ Suivant"))
    player.controls.rewind_clicked.connect(lambda: print("◀ -10s"))
    player.controls.forward_clicked.connect(lambda: print("▶ +10s"))
    
    window.setCentralWidget(player)
    window.show()
    
    sys.exit(app.exec())
