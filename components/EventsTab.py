from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QScrollArea, QFrame
from PyQt6.QtCore import Qt
from EventForm import EventForm
from EventRow import EventRow

class EventsTab(QWidget):
    def __init__(self, video_duration=15*60):
        super().__init__()

        self.video_duration = video_duration
        self.event_rows = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5,5,5,5)

        # --- Scroll area pour contenir les EventRow + bouton ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        scroll_content = QFrame()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(scroll_content)
        main_layout.addWidget(self.scroll_area)

        # --- Bouton Ajouter événement ---
        self.btn_add_event = QPushButton("Ajouter événement")
        self.btn_add_event.setFixedWidth(150)  # largeur fixe, pas toute la fenêtre
        self.btn_add_event.setMaximumHeight(30)
        self.scroll_layout.addWidget(self.btn_add_event, alignment=Qt.AlignmentFlag.AlignLeft)
        self.btn_add_event.clicked.connect(self.open_event_form)

    def open_event_form(self):
        self.form = EventForm()
        self.form.event_created.connect(self.add_event)
        self.form.show()

    def add_event(self, event_data):
        """
        Ajoute un EventRow juste avant le bouton Ajouter
        """
        occurrences = [(event_data.get('start', 0), event_data.get('end', 0))]
        row = EventRow(
            event_name=event_data['name'],
            event_type=event_data['type'],
            event_occurrences=occurrences,
            video_duration=self.video_duration
        )

        # Insérer juste avant le bouton
        self.scroll_layout.insertWidget(len(self.event_rows), row)
        self.event_rows.append(row)
