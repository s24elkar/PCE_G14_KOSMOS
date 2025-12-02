"""
Composant Courbe Tonale
Éditeur de courbe interactif pour ajuster la tonalité de l'image.
"""
import numpy as np
from typing import Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF


class InteractiveCurveWidget(QWidget):
    """
    Widget de dessin pour la courbe tonale interactive.
    """
    curve_changed = pyqtSignal(list)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.setMouseTracking(True)
        self.reset()

    def _map_point_to_widget(self, p: list) -> QPointF:
        """Convertit un point (0-255) en coordonnées du widget."""
        w, h = self.width(), self.height()
        x = (p[0] / 255.0) * w
        y = h - (p[1] / 255.0) * h
        return QPointF(x, y)

    def _map_pos_to_point(self, pos: QPointF) -> list:
        """Convertit une position du widget en point (0-255)."""
        w, h = self.width(), self.height()
        x = np.clip((pos.x() / w) * 255, 0, 255)
        y = np.clip(((h - pos.y()) / h) * 255, 0, 255)
        return [int(x), int(y)]

    def reset(self) -> None:
        """Réinitialise les points de contrôle à une ligne droite."""
        # Plus de points pour un contrôle plus fin (0, 25%, 50%, 75%, 100%)
        self.points = [[0, 0], [64, 64], [128, 128], [192, 192], [255, 255]]
        self.dragging_point_index = -1
        self._emit_curve()
        self.update()

    def _emit_curve(self) -> None:
        """Calcule la LUT à partir des points et émet le signal."""
        x_coords = [p[0] for p in self.points]
        y_coords = [p[1] for p in self.points]
        lut = np.interp(np.arange(256), x_coords, y_coords)
        lut = np.clip(lut, 0, 255).astype(np.uint8)
        self.curve_changed.emit(lut.tolist())

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#182025"))

        # Grille
        grid_pen = QPen(QColor("#303940"), 0.5)
        painter.setPen(grid_pen)
        for i in range(1, 4):
            x = self.width() * i / 4
            y = self.height() * i / 4
            painter.drawLine(int(x), 0, int(x), self.height())
            painter.drawLine(0, int(y), self.width(), int(y))

        # Ligne diagonale de référence
        painter.setPen(QPen(QColor("#404950"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(0, self.height(), self.width(), 0)

        # Courbe
        curve_pen = QPen(QColor("#2196F3"), 2)
        painter.setPen(curve_pen)
        mapped_points = [self._map_point_to_widget(p) for p in self.points]
        poly = QPolygonF(mapped_points)
        painter.drawPolyline(poly)

        # Points de contrôle
        for i, p in enumerate(mapped_points):
            is_endpoint = (i == 0 or i == len(mapped_points) - 1)
            radius = 4 if is_endpoint else 5
            painter.setBrush(QColor("#2196F3") if not is_endpoint else QColor("white"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(p, radius, radius)

            # Afficher les coordonnées si le point est en cours de déplacement
            if i == self.dragging_point_index:
                val = self.points[i]
                text = f"({val[0]}, {val[1]})"
                painter.setPen(QColor("white"))
                # Positionner le texte un peu au-dessus du point
                painter.drawText(int(p.x()) + 10, int(p.y()) - 10, text)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            for i, p in enumerate(self.points):
                # Ne pas permettre de déplacer les points de fin horizontalement
                if i == 0 or i == len(self.points) - 1:
                    continue
                
                widget_p = self._map_point_to_widget(p)
                if (QPointF(event.pos()) - widget_p).manhattanLength() < 10:
                    self.dragging_point_index = i
                    self.setCursor(Qt.CursorShape.ClosedHandCursor)
                    break

    def mouseMoveEvent(self, event) -> None:
        if self.dragging_point_index != -1:
            new_point = self._map_pos_to_point(event.pos())
            
            # Contraintes de déplacement
            prev_x = self.points[self.dragging_point_index - 1][0]
            next_x = self.points[self.dragging_point_index + 1][0]
            new_point[0] = np.clip(new_point[0], prev_x + 1, next_x - 1)

            self.points[self.dragging_point_index] = new_point
            self._emit_curve()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging_point_index = -1
            self.setCursor(Qt.CursorShape.ArrowCursor)


class ToneCurveEditor(QWidget):
    """
    Composant complet de l'éditeur de courbe tonale, avec en-tête.
    """
    curve_changed = pyqtSignal(list)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # En-tête
        header = QLabel("Courbe Tonale")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(24) # Hauteur fixe réduite
        header.setStyleSheet("""
            QLabel {
                background-color: #111827;
                color: #e5e7eb;
                font-size: 11px;
                font-weight: 700;
                padding: 0px;
                border-bottom: 1px solid #1f2937;
            }
        """)
        main_layout.addWidget(header)

        # Container pour la courbe
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(2, 2, 2, 2)

        self.curve_widget = InteractiveCurveWidget()
        self.curve_widget.curve_changed.connect(self.curve_changed.emit)
        container_layout.addWidget(self.curve_widget)

        main_layout.addWidget(container, 1) # Le container prend tout l'espace restant

        # Bouton de réinitialisation
        reset_button = QPushButton("Réinitialiser la courbe")
        reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #9CA3AF;
                border: none;
                font-size: 12px;
                padding: 4px;
            }
            QPushButton:hover {
                color: #E5E7EB;
                text-decoration: underline;
            }
        """)
        reset_button.clicked.connect(self.reset)
        container_layout.addWidget(reset_button, 0, Qt.AlignmentFlag.AlignRight)

    def reset(self) -> None:
        """Réinitialise la courbe à son état par défaut."""
        self.curve_widget.reset()
