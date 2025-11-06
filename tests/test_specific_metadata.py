from PyQt6.QtWidgets import QMessageBox

from components.specific_metadata import SpecificMetadataWidget
from controllers.video_metadata_controller import VideoMetadataController
from models.video_metadata_model import VideoMetadataModel
from views.tri_view import TriView


def test_specific_metadata_widget_emits_video_payload(qapp):
    widget = SpecificMetadataWidget()
    widget.set_video("video1.mp4", {"espece": "raie"})

    captured = {}

    def _capture(video_name, payload):
        captured["video"] = video_name
        captured["payload"] = payload

    widget.save_requested.connect(_capture)
    widget.ok_button.click()

    assert captured["video"] == "video1.mp4"
    assert captured["payload"]["espece"] == "raie"


def test_video_metadata_controller_updates_model_and_shows_success(qapp, monkeypatch):
    view = TriView()
    model = VideoMetadataModel()
    controller = VideoMetadataController(view, model)

    messages = []
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args: messages.append(args[2]),
    )

    controller.set_current_video("clip_A.mp4")
    widget = view.specific_metadata_widget
    widget._inputs["espece"].setText("Raie manta")
    widget.ok_button.click()

    assert model.get_metadata("clip_A.mp4")["espece"] == "Raie manta"
    assert messages[-1] == "Modifié avec succès"
