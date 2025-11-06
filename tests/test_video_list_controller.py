from PyQt6.QtWidgets import QInputDialog, QMessageBox

from controllers.video_list_controller import VideoListController
from controllers.video_metadata_controller import VideoMetadataController
from models.video_list_model import VideoItem, VideoListModel
from models.video_metadata_model import VideoMetadataModel
from views.tri_view import TriView


def _make_controller():
    videos = [
        VideoItem("clip1.mp4", "2024-10-01", "00:30"),
        VideoItem("clip2.mp4", "2024-10-02", "00:45"),
    ]
    model = VideoListModel(videos)
    view = TriView()
    metadata_model = VideoMetadataModel()
    metadata_controller = VideoMetadataController(view, metadata_model)
    controller = VideoListController(view, model, metadata_controller)
    return view, model, metadata_model, metadata_controller, controller


def test_video_rename_updates_model_and_view(qapp, monkeypatch):
    view, model, metadata_model, metadata_controller, controller = _make_controller()

    view.video_list_widget.select_video("clip1.mp4")
    controller.on_video_selected("clip1.mp4")

    metadata_model.set_metadata("clip1.mp4", {"espece": "Raie"})

    monkeypatch.setattr(
        QInputDialog,
        "getText",
        lambda *args, **kwargs: ("clip1_final.mp4", True),
    )

    messages = []
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args: messages.append(args[2]),
    )

    view.video_list_widget.rename_button.click()

    assert model.get_video("clip1_final.mp4") is not None
    assert view.video_list_widget.current_video() == "clip1_final.mp4"
    assert messages[-1] == "Vidéo renommée en 'clip1_final.mp4'."
    assert metadata_model.get_metadata("clip1.mp4") == {}
    assert view.specific_metadata_widget.video_label.text() == "Vidéo sélectionnée : clip1_final.mp4"
    assert metadata_model.get_metadata("clip1_final.mp4")["espece"] == "Raie"


def test_video_delete_confirms_and_clears_selection(qapp, monkeypatch):
    view, model, metadata_model, metadata_controller, controller = _make_controller()

    view.video_list_widget.select_video("clip2.mp4")
    controller.on_video_selected("clip2.mp4")

    metadata_model.set_metadata("clip2.mp4", {"espece": "Requin"})

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    info_messages = []
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args: info_messages.append(args[2]),
    )

    view.video_list_widget.delete_button.click()

    assert model.get_video("clip2.mp4") is None
    assert view.video_list_widget.current_video() is None
    assert not view.video_list_widget.rename_button.isEnabled()
    assert info_messages[-1] == "Vidéo 'clip2.mp4' supprimée."
    assert metadata_model.get_metadata("clip2.mp4") == {}
    assert view.specific_metadata_widget.video_label.text() == "Aucune vidéo sélectionnée"


def test_video_rename_handles_duplicates(qapp, monkeypatch):
    view, model, metadata_model, metadata_controller, controller = _make_controller()

    view.video_list_widget.select_video("clip1.mp4")
    controller.on_video_selected("clip1.mp4")

    monkeypatch.setattr(
        QInputDialog,
        "getText",
        lambda *args, **kwargs: ("clip2.mp4", True),
    )

    warnings = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args: warnings.append(args[2]),
    )

    view.video_list_widget.rename_button.click()

    assert "existe déjà" in warnings[-1]
    assert model.get_video("clip1.mp4") is not None
