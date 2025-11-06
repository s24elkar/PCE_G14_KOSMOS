import pytest

from components.EventForm import EventForm
from components.EventRow import TimelineRow, EventRow
from components.EventsTab import EventsTab


def test_event_form_mmss_to_seconds():
    form = EventForm()
    assert form.mmss_to_seconds("01:30") == 90
    assert form.mmss_to_seconds("45") == 45
    assert form.mmss_to_seconds("invalid") is None


def test_event_form_emits_event(qapp, monkeypatch):
    form = EventForm()

    emitted = []
    form.event_created.connect(emitted.append)

    form.name_input.setText("Test")
    form.start_input.setText("00:05")
    form.end_input.setText("00:10")

    # Ensure message boxes do not block if triggered unexpectedly
    monkeypatch.setattr("components.EventForm.QMessageBox.warning", lambda *args, **kwargs: None)

    form.add_event()

    assert emitted == [
        {"name": "Test", "type": "Poisson", "start": 5, "end": 10}
    ]


def test_timeline_row_updates_occurrences(qapp):
    timeline = TimelineRow(video_duration=120)
    timeline.set_occurrences([(10, 20), (30, 30)])
    assert timeline.event_occurrences == [(10, 20), (30, 30)]


def test_event_row_and_tab_add_event(qapp):
    row = EventRow("Test", "Type", [(0, 5)], video_duration=60)
    assert row.timeline.event_occurrences == [(0, 5)]
    assert "Test" in row.name_label.text()

    tab = EventsTab(video_duration=60)
    tab.add_event({"name": "Event1", "type": "TypeA", "start": 5, "end": 15})

    assert len(tab.event_rows) == 1
    added_row = tab.event_rows[0]
    assert added_row.timeline.event_occurrences == [(5, 15)]
