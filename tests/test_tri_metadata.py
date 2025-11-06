from PyQt6.QtWidgets import QMessageBox

from components.common_metadata import CommonMetadataWidget
from controllers.tri_controller import TriController
from models.metadata_model import MetadataModel
from views.tri_view import TriView


def test_common_metadata_widget_emits_save(qapp):
    widget = CommonMetadataWidget()
    widget.set_metadata({"date": "2024-10-01"})

    captured = {}

    def _capture(payload):
        captured.update(payload)

    widget.save_requested.connect(_capture)
    widget.ok_button.click()

    assert captured == {"date": "2024-10-01"}
    assert widget.scroll_area.widget().layout().rowCount() == 1


def test_tri_controller_updates_model_and_shows_dialog(qapp, monkeypatch):
    initial = {"date": "2024-10-01", "lieu": "Atlantique"}
    model = MetadataModel(initial)
    view = TriView()
    controller = TriController(view, model)

    assert view.common_metadata_widget.metadata() == initial

    messages = []
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args: messages.append(args[2]),
    )

    view.common_metadata_widget._inputs["lieu"].setText("Pacifique")
    view.common_metadata_widget.ok_button.click()

    assert model.get_common_metadata()["lieu"] == "Pacifique"
    assert messages[-1] == "Modifié avec succès"
