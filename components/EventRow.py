from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor

class TimelineRow(QWidget):
    def __init__(self, event_occurrences=None, video_duration=100, parent=None):
        super().__init__(parent)
        self.event_occurrences = event_occurrences if event_occurrences else []
        self.video_duration = video_duration  # en secondes
        self.setMinimumHeight(30)
        self.setMaximumHeight(30)

    def set_occurrences(self, occurrences):
        self.event_occurrences = occurrences
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.event_occurrences:
            return

        painter = QPainter(self)
        w = self.width()
        h = self.height()

        # Fond clair pour la timeline
        painter.fillRect(0, 0, w, h, QColor("#2c2f38"))

        # Dessiner chaque occurrence
        for occ in self.event_occurrences:
            start, end = occ  # timestamps en secondes
            x_start = int((start / self.video_duration) * w)
            x_end = int((end / self.video_duration) * w)
            color = QColor("#6c63ff")

            if start == end:
                # Point
                painter.fillRect(x_start-2, h//4, 4, h//2, color)
            else:
                # Barre
                painter.fillRect(x_start, h//4, max(2, x_end - x_start), h//2, color)

        painter.end()


class EventRow(QWidget):
    def __init__(self, event_name, event_type, event_occurrences=None, video_duration=100, parent=None):
        super().__init__(parent)

        self.name_label = QLabel(f"{event_name} ({event_type})")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.timeline = TimelineRow(event_occurrences, video_duration)

        layout = QHBoxLayout()
        layout.addWidget(self.name_label, 1)
        layout.addWidget(self.timeline, 3)
        layout.setContentsMargins(5, 0, 5, 0)
        self.setLayout(layout)
